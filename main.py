from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager
from jose import jwt, JWTError
import hashlib

# Your local imports
from database import db
from audit_service import log_access_event
from auth import verify_password, create_access_token, oauth2_scheme

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(title="WardVault Gateway", lifespan=lifespan)

# CORS configuration for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REQUEST MODELS ---
class RecordAccessRequest(BaseModel):
    patient_id: str
    client_ward_id: str = "" # No longer mandatory for JAJA
    is_emergency: bool = False
    override_reason: str = None

class ClinicalNoteRequest(BaseModel):
    patient_id: str
    note_text: str
    
class NoteCorrectionRequest(BaseModel):
    patient_id: str
    original_note_id: int
    corrected_text: str
    reason: str

@app.get("/health")
async def health_check():
    return {"status": "online", "system": "WardVault Gateway"}


# --- 1. THE LOGIN ENDPOINT ---
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with db.legacy_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, password_hash, speciality, organization FROM providers WHERE id = $1", 
            form_data.username
        )
        
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect ID or password")
        
        access_token = create_access_token(
            data={
                "sub": user["id"], 
                "role": user["speciality"], 
                "org": user.get("organization", "ORG-UCH")
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}


# --- 2. THE TOKEN DECODER ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "wardvault-super-secret-hackathon-key", algorithms=["HS256"])
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload 
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- 3. THE SECURE MULTI-TENANT ACCESS ROUTE ---
@app.post("/api/records/access")
async def access_patient_record(
    req: RecordAccessRequest, 
    user: dict = Depends(get_current_user)
):
    current_user_id = user["sub"]
    provider_org = str(user.get("org", "")).upper()
    provider_role = str(user.get("role", "")).strip()

    async with db.legacy_pool.acquire() as conn:
        patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", req.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found in database")

        patient_org = str(patient.get("organization", "")).upper()

        # STRICT CROSS-TENANT ISOLATION (Blocks JAJA from UCH and UCH from JAJA)
        is_jaja_staff = "JAJA" in provider_org
        is_jaja_patient = "JAJA" in patient_org

        if is_jaja_staff != is_jaja_patient:
            await log_access_event(current_user_id, "CROSS_TENANT_VIOLATION_BLOCKED", req.patient_id, f"Staff org ({provider_org}) attempted to access cross-facility patient ({patient_org})")
            raise HTTPException(status_code=403, detail="Cross-Tenant Security Violation: Access between JAJA Clinic and UCH Hospital is strictly prohibited.")

        # HARD BLOCK FOR NON-CLINICAL STAFF
        if provider_role in ["Billing Clerk", "IT Admin", "Clerk"]:
            await log_access_event(current_user_id, "ACCESS_DENIED_NON_CLINICAL", req.patient_id, "Non-clinical staff restricted")
            raise HTTPException(
                status_code=403, 
                detail=f"Access Denied: Administrative and IT roles ('{provider_role}') are strictly prohibited from viewing clinical charts."
            )

        is_authorized = False
        action_name = ""

        # ABAC EVALUATION: JAJA vs UCH
        if is_jaja_staff:
            is_authorized = True
            action_name = "JAJA_AMBULATORY_ACCESS_GRANTED"
        else:
            core_speciality = provider_role.split()[0].lower()
            patient_ward = str(patient["ward_id"]).lower()

            if core_speciality in patient_ward:
                is_authorized = True
                action_name = "UCH_RECORD_ACCESSED"
            else:
                action_name = "UCH_WARD_MISMATCH_DENIED"

        # EMERGENCY OVERRIDE
        if not is_authorized and req.is_emergency:
            doctor_roles = ["Emergency Medicine", "Cardiology", "Neurology", "Pediatrics", "Surgery"]
            if provider_role not in doctor_roles:
                await log_access_event(current_user_id, "UNAUTHORIZED_OVERRIDE_ATTEMPT", req.patient_id, f"Role ({provider_role}) attempted override")
                raise HTTPException(status_code=403, detail="Emergency override denied: Only authorized physicians (Doctors) can break glass.")
            
            if not req.override_reason or len(req.override_reason.strip()) < 3:
                raise HTTPException(status_code=400, detail="Override justification required for compliance auditing.")

            audit_entry = await log_access_event(current_user_id, "EMERGENCY_OVERRIDE_GRANTED", req.patient_id, req.override_reason)
            return {
                "status": "GRANTED_VIA_OVERRIDE", 
                "patient": dict(patient), 
                "audit": {
                    "current_hash": audit_entry.get("current_hash", "787a9deba783aed400279053024e3fa9..."),
                    "timestamp": str(audit_entry.get("timestamp", ""))
                }
            }

        # STANDARD DENIAL
        if not is_authorized:
            audit_entry = await log_access_event(current_user_id, action_name, req.patient_id, "Ward mismatch")
            raise HTTPException(status_code=403, detail={"message": "Access Denied: Patient is outside your assigned ward.", "audit": audit_entry})

        # SUCCESS PATH
        audit_entry = await log_access_event(current_user_id, action_name, req.patient_id)
        return {
            "status": "GRANTED", 
            "patient": dict(patient), 
            "audit": {
                "current_hash": audit_entry.get("current_hash", "787a9deba783aed400279053024e3fa9..."),
                "timestamp": str(audit_entry.get("timestamp", ""))
            }
        }


# --- 4. DYNAMIC CENSUS ENDPOINT (MULTI-TENANT SECURED) ---
@app.get("/api/patients")
async def get_all_patients(user: dict = Depends(get_current_user)):
    try:
        staff_org = str(user.get("org", "")).upper()
        staff_role = str(user.get("role", "")).strip()
        
        if staff_role in ["Billing Clerk", "IT Admin", "Clerk"]:
            return []
            
        async with db.legacy_pool.acquire() as conn:
            if "JAJA" in staff_org:
                query = "SELECT id, first, last, 'Clinic - JAJA Ambulatory' AS ward_id FROM patients WHERE organization ILIKE '%JAJA%' ORDER BY id ASC"
                patients = await conn.fetch(query)
            else:
                core_speciality = staff_role.split()[0].lower()
                query = "SELECT id, first, last, ward_id FROM patients WHERE organization ILIKE '%UCH%' AND ward_id ILIKE $1 ORDER BY ward_id ASC"
                patients = await conn.fetch(query, f"%{core_speciality}%")
            
            return [{"id": str(p["id"]), "name": f"{p['first']} {p['last']}", "ward_id": str(p["ward_id"])} for p in patients]
    except Exception as e:
        print(f"🔥 FETCH PATIENTS ERROR: {e}")
        return []


# --- 5. THE AUDIT LOG ENDPOINT (FOR THE CPO DASHBOARD) ---
@app.get("/api/audit-logs")
async def get_audit_logs():
    async with db.audit_pool.acquire() as conn:
        logs = await conn.fetch("SELECT timestamp, user_id, target_patient_id, action, current_hash FROM audit_log ORDER BY timestamp DESC LIMIT 15")
        return [
            {
                "timestamp": str(l["timestamp"]),
                "provider_id": l["user_id"],              
                "patient_id": l["target_patient_id"],    
                "action": l["action"],
                "current_hash": l["current_hash"]
            } for l in logs
        ]


# --- 5B. ADMIN CLINICAL NOTES INSPECTOR ENDPOINT ---
@app.get("/api/admin/clinical-notes")
async def get_admin_clinical_notes():
    async with db.legacy_pool.acquire() as conn:
        notes = await conn.fetch("""
            SELECT id, patient_id, provider_id, note_text, timestamp, correction_reason, supersedes_note_id 
            FROM clinical_notes 
            ORDER BY timestamp DESC LIMIT 50
        """)
        return [
            {
                "id": n["id"],
                "patient_id": n["patient_id"],
                "provider_id": n["provider_id"],
                "note_text": n["note_text"],
                "timestamp": str(n["timestamp"]),
                "correction_reason": n["correction_reason"],
                "supersedes_note_id": n["supersedes_note_id"]
            } for n in notes
        ]


# --- 6. APPEND-ONLY CORRECTION WORKFLOW ---
@app.post("/api/records/notes")
async def add_clinical_note(req: ClinicalNoteRequest, user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        new_note_id = await conn.fetchval(
            "INSERT INTO clinical_notes (patient_id, provider_id, note_text) VALUES ($1, $2, $3) RETURNING id",
            req.patient_id, user["sub"], req.note_text
        )
        await log_access_event(user["sub"], "CLINICAL_NOTE_ADDED", req.patient_id, f"Note ID: {new_note_id}")
        return {"status": "success", "note_id": new_note_id}

@app.post("/api/records/notes/correct")
async def correct_clinical_note(req: NoteCorrectionRequest, user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        original = await conn.fetchrow("SELECT id FROM clinical_notes WHERE id = $1", req.original_note_id)
        if not original:
            raise HTTPException(status_code=404, detail="Original record not found.")

        correction_id = await conn.fetchval(
            """INSERT INTO clinical_notes (patient_id, provider_id, note_text, correction_reason, supersedes_note_id) 
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            req.patient_id, user["sub"], req.corrected_text, req.reason, req.original_note_id
        )
        
        await log_access_event(user["sub"], "RECORD_CORRECTED", req.patient_id, f"Correction ID: {correction_id} overrides Note ID: {req.original_note_id}. Reason: {req.reason}")
        return {"status": "Correction appended successfully", "correction_id": correction_id}


# --- 7. CRYPTOGRAPHIC VERIFICATION ENDPOINT ---
@app.get("/api/audit/verify")
async def verify_audit_ledger():
    try:
        async with db.audit_pool.acquire() as conn:
            logs = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")
            
            if not logs:
                return {"status": "SECURE", "message": "Ledger is empty."}

            expected_previous = "0" * 64
            
            for row in logs:
                if row.get('previous_hash') != expected_previous:
                    return {"status": "COMPROMISED", "broken_entry": row['entry_id'], "detail": "Chain link broken. Previous hash does not match."}
                
                user_id = row.get('user_id', '') or ''
                action = row.get('action', '') or ''
                patient_id = row.get('target_patient_id', '') or ''
                reason = row.get('reason', '') or ''
                prev_hash = row.get('previous_hash', '') or ''
                
                payload = f"{user_id}|{action}|{patient_id}|{reason}|{prev_hash}"
                recomputed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                
                if recomputed_hash != row.get('current_hash'):
                    return {"status": "COMPROMISED", "broken_entry": row['entry_id'], "detail": "Data altered! Cryptographic verification failed."}
                
                expected_previous = row.get('current_hash')
                
            return {"status": "SECURE", "message": f"Successfully verified {len(logs)} cryptographic links."}
    except Exception as e:
        print(f"🔥 VERIFY ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))