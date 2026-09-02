from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager
from jose import jwt, JWTError

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
    client_ward_id: str
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
        
        # Embed role and organization into the token payload
        access_token = create_access_token(
            data={"sub": user["id"], "role": user["speciality"], "org": user.get("organization", "ORG-UCH")}
        )
        return {"access_token": access_token, "token_type": "bearer"}

# --- 2. THE TOKEN DECODER ---
async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "wardvault-super-secret-hackathon-key", algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- 3. THE SECURE MULTI-TENANT ACCESS ROUTE ---
@app.post("/api/records/access")
async def access_patient_record(
    req: RecordAccessRequest, 
    current_user_id: str = Depends(get_current_user_id)
):
    async with db.legacy_pool.acquire() as conn:
        # Fetch staff details including organization
        staff = await conn.fetchrow(
            """SELECT p.id, p.speciality, p.organization, s.ward_id, s.is_active 
               FROM providers p 
               LEFT JOIN active_shifts s ON p.id = s.provider_id 
               WHERE p.id = $1""",
            current_user_id
        )
        if not staff:
            raise HTTPException(status_code=404, detail="Provider not found")

        provider_org = staff.get("organization", "ORG-UCH")
        provider_role = staff["speciality"]

        # --- MULTI-TENANT ABAC EVALUATION ---
        is_authorized = False
        action_name = ""

        # Scenario A: JAJA CLINIC (Ambulatory / Walk-in / No Wards)
        if provider_org == "ORG-JAJA":
            clinical_roles = ["Cardiology", "Neurology", "Pediatrics", "Emergency Medicine", "Surgery"]
            if provider_role in clinical_roles:
                is_authorized = True
                action_name = "JAJA_AMBULATORY_ACCESS_GRANTED"
            else:
                action_name = "JAJA_ACCESS_DENIED_NON_CLINICAL"

        # Scenario B: UCH HOSPITAL (Inpatient / Strict Wards)
        else:
            is_authorized = (staff["is_active"] is True and staff["ward_id"] == req.client_ward_id)
            if is_authorized:
                action_name = "UCH_RECORD_ACCESSED"

        # Handle Authorization Result
        if not is_authorized and req.is_emergency:
            # Enforce Emergency Override Rules: STRICTLY DOCTORS ONLY (Exclude Nurses and non-clinical roles)
            doctor_roles = ["Emergency Medicine", "Cardiology", "Neurology", "Pediatrics", "Surgery"]
            
            if provider_role not in doctor_roles:
                audit_entry = await log_access_event(
                    current_user_id, 
                    "UNAUTHORIZED_OVERRIDE_ATTEMPT", 
                    req.patient_id, 
                    f"Unauthorized role ({provider_role}) attempted emergency override"
                )
                raise HTTPException(
                    status_code=403, 
                    detail=f"Emergency override denied: '{provider_role}' is restricted. Only attending physicians (Doctors) are authorized to execute break-glass overrides."
                )
            
            # Ensure override reason is provided for compliance auditing
            if not req.override_reason or len(req.override_reason.strip()) < 3:
                raise HTTPException(
                    status_code=400, 
                    detail="Override justification required for compliance auditing."
                )

            audit_entry = await log_access_event(current_user_id, "EMERGENCY_OVERRIDE_GRANTED", req.patient_id, req.override_reason)
            patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", req.patient_id)
            
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found in database")
                
            return {"status": "GRANTED_VIA_OVERRIDE", "patient": dict(patient), "audit": audit_entry}

        if not is_authorized:
            audit_entry = await log_access_event(current_user_id, action_name or "ACCESS_DENIED", req.patient_id, "Shift inactive, ward mismatch, or policy restriction")
            raise HTTPException(status_code=403, detail={"message": "Access Denied", "audit": audit_entry})

        # Success path (Standard Access or Jaja Ambulatory Access)
        audit_entry = await log_access_event(current_user_id, action_name, req.patient_id)
        patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", req.patient_id)
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found in database")
            
        return {"status": "GRANTED", "patient": dict(patient), "audit": audit_entry}

# --- 4. THE AUDIT LOG ENDPOINT (FOR THE CPO DASHBOARD) ---
@app.get("/api/audit-logs")
async def get_audit_logs():
    async with db.audit_pool.acquire() as conn:
        logs = await conn.fetch(
            "SELECT timestamp, user_id, target_patient_id, action, current_hash FROM audit_log ORDER BY timestamp DESC LIMIT 15"
        )
        
        return [
            {
                "timestamp": str(log["timestamp"]),
                "provider_id": log["user_id"],              
                "patient_id": log["target_patient_id"],    
                "action": log["action"],
                "current_hash": log["current_hash"]
            } for log in logs
        ]

# --- 5. APPEND-ONLY CORRECTION WORKFLOW ---
@app.post("/api/records/notes")
async def add_clinical_note(req: ClinicalNoteRequest, current_user_id: str = Depends(get_current_user_id)):
    async with db.legacy_pool.acquire() as conn:
        new_note_id = await conn.fetchval(
            "INSERT INTO clinical_notes (patient_id, provider_id, note_text) VALUES ($1, $2, $3) RETURNING id",
            req.patient_id, current_user_id, req.note_text
        )
        await log_access_event(current_user_id, "CLINICAL_NOTE_ADDED", req.patient_id, f"Note ID: {new_note_id}")
        return {"status": "success", "note_id": new_note_id}

@app.post("/api/records/notes/correct")
async def correct_clinical_note(req: NoteCorrectionRequest, current_user_id: str = Depends(get_current_user_id)):
    async with db.legacy_pool.acquire() as conn:
        original = await conn.fetchrow("SELECT id FROM clinical_notes WHERE id = $1", req.original_note_id)
        if not original:
            raise HTTPException(status_code=404, detail="Original record not found.")

        # Inserts correction pointing back to the original to prevent silent overwrites[cite: 1]
        correction_id = await conn.fetchval(
            """INSERT INTO clinical_notes (patient_id, provider_id, note_text, correction_reason, supersedes_note_id) 
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            req.patient_id, current_user_id, req.corrected_text, req.reason, req.original_note_id
        )
        
        await log_access_event(
            current_user_id, 
            "RECORD_CORRECTED", 
            req.patient_id, 
            f"Correction ID: {correction_id} overrides Note ID: {req.original_note_id}. Reason: {req.reason}"
        )
        return {"status": "Correction appended successfully", "correction_id": correction_id}

import hashlib

# --- 6. CRYPTOGRAPHIC VERIFICATION ENDPOINT (FOR LIVE DEMO) ---
@app.get("/api/audit/verify")
async def verify_audit_ledger():
    try:
        async with db.audit_pool.acquire() as conn:
            # Fetch all logs in order to walk the chain
            logs = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")
            
            if not logs:
                return {"status": "SECURE", "message": "Ledger is empty."}

            expected_previous = "0" * 64
            
            for row in logs:
                # 1. Check if previous hash link is broken
                if row.get('previous_hash') != expected_previous:
                    return {
                        "status": "COMPROMISED", 
                        "broken_entry": row['entry_id'],
                        "detail": "Chain link broken. Previous hash does not match."
                    }
                
                # 2. Recompute current hash to see if data was secretly changed
                # Using .get() with fallback to empty string so NULL database values don't crash the server
                user_id = row.get('user_id', '') or ''
                action = row.get('action', '') or ''
                patient_id = row.get('target_patient_id', '') or ''
                reason = row.get('reason', '') or ''
                prev_hash = row.get('previous_hash', '') or ''
                
                payload = f"{user_id}|{action}|{patient_id}|{reason}|{prev_hash}"
                recomputed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                
                if recomputed_hash != row.get('current_hash'):
                    return {
                        "status": "COMPROMISED", 
                        "broken_entry": row['entry_id'],
                        "detail": f"Data altered! Expected: {recomputed_hash[:10]}... Found: {str(row.get('current_hash'))[:10]}..."
                    }
                
                expected_previous = row.get('current_hash')
                
            return {"status": "SECURE", "message": f"Successfully verified {len(logs)} cryptographic links."}
    except Exception as e:
        print(f"🔥 VERIFY ERROR: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

# --- 7. DYNAMIC CENSUS ENDPOINT (MULTI-TENANT SECURED) ---
@app.get("/api/patients")
async def get_all_patients(user: dict = Depends(get_current_user_id)):
    try:
        # Extract the organization (e.g., ORG-UCH or ORG-JAJA) from the logged-in user's token
        staff_org = user.get("organization")
        
        async with db.legacy_pool.acquire() as conn:
            # Multi-Tenant Filter: ONLY fetch patients where the organization matches the staff!
            query = """
                SELECT id, first, last, ward_id 
                FROM patients 
                WHERE deathdate IS NULL AND organization = $1 
                ORDER BY ward_id ASC
            """
            patients = await conn.fetch(query, staff_org)
            
            return [
                {
                    "id": str(p["id"]), 
                    "name": f"{p['first']} {p['last']}", 
                    "ward_id": str(p["ward_id"])
                } for p in patients
            ]
    except Exception as e:
        print(f"🔥 FETCH PATIENTS ERROR: {e}")
        return []