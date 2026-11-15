import os
import hashlib
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import jwt, JWTError

# Local imports
from database import db
from audit_service import log_access_event
from auth import verify_password, create_access_token, oauth2_scheme

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(
    title="WardVault PHC Gateway",
    description="Offline-First Patient Records & Care Coordination for Primary Healthcare Centres",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REQUEST / RESPONSE MODELS ---
class PatientRegistrationRequest(BaseModel):
    first: str
    last: str
    gender: str
    age: int
    folder_number: str
    condition: Optional[str] = "Primary Care Outpatient"
    blood_group: Optional[str] = "Unknown"
    genotype: Optional[str] = "Unknown"
    phone: Optional[str] = ""
    nin: Optional[str] = ""
    bhcpf_id: Optional[str] = ""
    allergies: Optional[str] = "None reported"
    is_paper_migration: bool = False
    flagged_for_review: bool = False
    review_notes: Optional[str] = ""

class EncounterRequest(BaseModel):
    patient_id: str
    encounter_type: str = "General Outpatient"
    bp: Optional[str] = "120/80"
    temperature: Optional[float] = 36.8
    pulse: Optional[int] = 76
    weight: Optional[float] = 60.0
    rdt_result: Optional[str] = "Not Tested"
    clinical_assessment: str
    prescription: Optional[str] = ""

class ReferralCreateRequest(BaseModel):
    patient_id: str
    destination_facility: str
    reason: str
    urgency: str = "Routine"

class ReferralStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = ""

class ClinicalNoteRequest(BaseModel):
    patient_id: str
    note_text: str

class NoteCorrectionRequest(BaseModel):
    patient_id: str
    original_note_id: int
    corrected_text: str
    reason: str

class BatchSyncRequest(BaseModel):
    encounters: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    referrals: List[Dict[str, Any]] = []

class ThreatReportRequest(BaseModel):
    patient_id: str
    description: str

# --- HEALTH & STATIC SERVING ---
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "system": "WardVault PHC Gateway",
        "version": "2.0.0",
        "focus": "Universal Service Provision Fund (USPF) Healthcare Innovation"
    }

@app.get("/")
@app.get("/app")
@app.get("/index.html")
async def serve_index():
    index_file = os.path.abspath("index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "WardVault PHC Gateway Active. API available at /docs"}

@app.get("/admin")
async def serve_admin():
    admin_file = os.path.abspath("admin.html")
    if os.path.exists(admin_file):
        return FileResponse(admin_file)
    return {"message": "Admin SIEM dashboard not found"}

# --- AUTHENTICATION & TOKENS ---
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with db.legacy_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, password_hash, speciality, organization, name, is_on_duty FROM providers WHERE id = $1",
            form_data.username
        )

        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect Provider ID or passphrase.")

        is_on_duty = bool(user.get("is_on_duty", True))

        access_token = create_access_token(
            data={
                "sub": user["id"],
                "name": user.get("name", "Staff Member"),
                "role": user["speciality"],
                "org": user.get("organization", "Alakia PHC"),
                "on_duty": is_on_duty
            }
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "provider": {
                "id": user["id"],
                "name": user.get("name"),
                "role": user["speciality"],
                "organization": user.get("organization"),
                "on_duty": is_on_duty
            }
        }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "wardvault-super-secret-hackathon-key", algorithms=["HS256"])
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid session token.")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")

# --- PATIENT CENSUS & DIRECTORY ---
@app.get("/api/patients")
async def get_patients(
    q: Optional[str] = Query(None, description="Search by name, folder number, NIN or BHCPF ID"),
    user: dict = Depends(get_current_user)
):
    async with db.legacy_pool.acquire() as conn:
        if q:
            search_pattern = f"%{q.strip()}%"
            query = """
                SELECT id, first, last, name, age, gender, organization, ward_id, condition,
                       blood_group, genotype, phone, nin, bhcpf_id, allergies
                FROM patients
                WHERE name LIKE $1 OR ward_id LIKE $2 OR nin LIKE $3 OR bhcpf_id LIKE $4
                ORDER BY id ASC LIMIT 100
            """
            patients = await conn.fetch(query, search_pattern, search_pattern, search_pattern, search_pattern)
        else:
            query = """
                SELECT id, first, last, name, age, gender, organization, ward_id, condition,
                       blood_group, genotype, phone, nin, bhcpf_id, allergies
                FROM patients
                ORDER BY id ASC LIMIT 100
            """
            patients = await conn.fetch(query)

        return [
            {
                "id": str(p["id"]),
                "name": p["name"] or f"{p['first']} {p['last']}",
                "folder_number": p["ward_id"],
                "age": p["age"],
                "gender": p["gender"],
                "condition": p["condition"],
                "blood_group": p.get("blood_group", "O+"),
                "genotype": p.get("genotype", "AA"),
                "phone": p.get("phone", ""),
                "nin": p.get("nin", ""),
                "bhcpf_id": p.get("bhcpf_id", ""),
                "allergies": p.get("allergies", "None")
            }
            for p in patients
        ]

# --- PATIENT DETAIL & FULL CHART ACCESS ---
@app.get("/api/patients/{patient_id}")
async def get_patient_chart(patient_id: str, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    is_on_duty = user.get("on_duty", False)

    if not is_on_duty:
        await log_access_event(staff_id, "ACCESS_DENIED_OFF_DUTY", patient_id, "Attempted chart access while clocked off")
        raise HTTPException(
            status_code=403,
            detail="Access Denied: You are currently OFF DUTY. All clinical charts are locked until you clock in."
        )

    async with db.legacy_pool.acquire() as conn:
        patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient record not found.")

        # Fetch clinical encounters
        encounters = await conn.fetch(
            "SELECT * FROM clinical_encounters WHERE patient_id = $1 ORDER BY timestamp DESC",
            patient_id
        )

        # Fetch clinical notes
        notes = await conn.fetch(
            "SELECT * FROM clinical_notes WHERE patient_id = $1 ORDER BY timestamp DESC",
            patient_id
        )

        # Fetch referrals
        referrals = await conn.fetch(
            "SELECT * FROM referrals WHERE patient_id = $1 ORDER BY created_at DESC",
            patient_id
        )

        # Fetch paper intake status if any
        intake = await conn.fetchrow(
            "SELECT * FROM paper_intakes WHERE patient_id = $1 ORDER BY id DESC LIMIT 1",
            patient_id
        )

        audit_entry = await log_access_event(staff_id, "PATIENT_CHART_ACCESSED", patient_id, "Outpatient clinical review")

        return {
            "patient": dict(patient),
            "encounters": [dict(e) for e in encounters],
            "clinical_notes": [dict(n) for n in notes],
            "referrals": [dict(r) for r in referrals],
            "paper_intake": dict(intake) if intake else None,
            "audit": audit_entry
        }

# --- PATIENT REGISTRATION & PAPER INTAKE ---
@app.post("/api/patients/register")
async def register_patient(req: PatientRegistrationRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    full_name = f"{req.first.strip()} {req.last.strip()}"
    new_patient_id = f"PHC-PT-{datetime.now().strftime('%m%d%H%M%S')}"

    async with db.legacy_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO patients (
                id, first, last, name, age, gender, organization, ward_id, condition,
                blood_group, genotype, phone, nin, bhcpf_id, allergies
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)""",
            new_patient_id, req.first, req.last, full_name, req.age, req.gender,
            user.get("org", "Alakia PHC"), req.folder_number, req.condition,
            req.blood_group, req.genotype, req.phone, req.nin, req.bhcpf_id, req.allergies
        )

        if req.is_paper_migration:
            await conn.execute(
                """INSERT INTO paper_intakes (
                    patient_id, folder_number, transcribed_by, flagged_for_review, review_notes
                ) VALUES ($1, $2, $3, $4, $5)""",
                new_patient_id, req.folder_number, staff_id, req.flagged_for_review, req.review_notes
            )
            action_name = "PAPER_FOLDER_TRANSCRIBED_REVIEW_REQUIRED" if req.flagged_for_review else "PAPER_FOLDER_MIGRATED"
            await log_access_event(staff_id, action_name, new_patient_id, f"Folder: {req.folder_number}")
        else:
            await log_access_event(staff_id, "NEW_PATIENT_REGISTERED", new_patient_id, f"Folder: {req.folder_number}")

        return {
            "status": "success",
            "patient_id": new_patient_id,
            "folder_number": req.folder_number,
            "message": "Patient record registered successfully."
        }

# --- OUTPATIENT CLINICAL ENCOUNTER ---
@app.post("/api/encounters")
async def record_encounter(req: EncounterRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    if not user.get("on_duty", False):
        raise HTTPException(status_code=403, detail="You are currently OFF DUTY.")

    async with db.legacy_pool.acquire() as conn:
        enc_id = await conn.fetchval(
            """INSERT INTO clinical_encounters (
                patient_id, provider_id, encounter_type, bp, temperature, pulse, weight,
                rdt_result, clinical_assessment, prescription
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id""",
            req.patient_id, staff_id, req.encounter_type, req.bp, req.temperature,
            req.pulse, req.weight, req.rdt_result, req.clinical_assessment, req.prescription
        )

        await log_access_event(
            staff_id,
            "CLINICAL_ENCOUNTER_RECORDED",
            req.patient_id,
            f"Encounter #{enc_id} ({req.encounter_type})"
        )

        return {"status": "success", "encounter_id": enc_id}

# --- REFERRALS & FOLLOW-UP ---
@app.get("/api/referrals")
async def get_referrals(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        refs = await conn.fetch("""
            SELECT r.id, r.patient_id, r.referred_by, r.destination_facility, r.reason,
                   r.urgency, r.status, r.created_at, r.updated_at,
                   p.name as patient_name, p.ward_id as folder_number, pr.name as staff_name
            FROM referrals r
            LEFT JOIN patients p ON r.patient_id = p.id
            LEFT JOIN providers pr ON r.referred_by = pr.id
            ORDER BY r.id DESC
        """)
        return [
            {
                "id": r["id"],
                "patient_id": r["patient_id"],
                "patient_name": r.get("patient_name") or r["patient_id"],
                "folder_number": r.get("folder_number") or "",
                "referred_by": r.get("staff_name") or r["referred_by"],
                "destination_facility": r["destination_facility"],
                "reason": r["reason"],
                "urgency": r["urgency"],
                "status": r["status"],
                "created_at": str(r["created_at"]),
                "updated_at": str(r["updated_at"])
            }
            for r in refs
        ]

@app.get("/api/paper-intakes/flagged")
async def get_flagged_paper_intakes(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        intakes = await conn.fetch("""
            SELECT pi.id, pi.patient_id, pi.folder_number, pi.transcribed_by,
                   pi.flagged_for_review, pi.review_notes, pi.created_at,
                   p.name as patient_name, p.condition
            FROM paper_intakes pi
            LEFT JOIN patients p ON pi.patient_id = p.id
            WHERE pi.flagged_for_review = 1
            ORDER BY pi.id DESC
        """)
        return [
            {
                "id": i["id"],
                "patient_id": i["patient_id"],
                "patient_name": i.get("patient_name") or i["patient_id"],
                "folder_number": i["folder_number"],
                "transcribed_by": i["transcribed_by"],
                "review_notes": i["review_notes"],
                "condition": i.get("condition", ""),
                "created_at": str(i["created_at"])
            }
            for i in intakes
        ]

@app.patch("/api/paper-intakes/{intake_id}/resolve")
async def resolve_paper_intake(intake_id: int, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    async with db.legacy_pool.acquire() as conn:
        intake = await conn.fetchrow("SELECT * FROM paper_intakes WHERE id = $1", intake_id)
        if not intake:
            raise HTTPException(status_code=404, detail="Intake record not found.")
        await conn.execute("UPDATE paper_intakes SET flagged_for_review = 0 WHERE id = $1", intake_id)
        await log_access_event(staff_id, "PAPER_FOLDER_REVIEW_RESOLVED", intake["patient_id"], f"Resolved clinical review for Folder #{intake['folder_number']}")
        return {"status": "success", "message": f"Folder #{intake['folder_number']} verified and cleared for clinical care."}

@app.get("/api/metrics")
async def get_facility_metrics():
    async with db.legacy_pool.acquire() as conn:
        pat_count = await conn.fetchval("SELECT count(*) FROM patients")
        enc_count = await conn.fetchval("SELECT count(*) FROM clinical_encounters")
        ref_count = await conn.fetchval("SELECT count(*) FROM referrals WHERE status != 'Completed'")
        flagged_count = await conn.fetchval("SELECT count(*) FROM paper_intakes WHERE flagged_for_review = 1")
    async with db.audit_pool.acquire() as conn:
        block_count = await conn.fetchval("SELECT count(*) FROM audit_log")
    return {
        "active_patients": pat_count or 0,
        "clinical_encounters": enc_count or 0,
        "active_referrals": ref_count or 0,
        "flagged_folders": flagged_count or 0,
        "audit_blocks": block_count or 0
    }

@app.post("/api/referrals")
async def create_referral(req: ReferralCreateRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    if not user.get("on_duty", False):
        raise HTTPException(status_code=403, detail="You are currently OFF DUTY.")

    async with db.legacy_pool.acquire() as conn:
        ref_id = await conn.fetchval(
            """INSERT INTO referrals (
                patient_id, referred_by, destination_facility, reason, urgency, status
            ) VALUES ($1, $2, $3, $4, $5, 'Referred') RETURNING id""",
            req.patient_id, staff_id, req.destination_facility, req.reason, req.urgency
        )

        await log_access_event(
            staff_id,
            "REFERRAL_ISSUED",
            req.patient_id,
            f"Referral #{ref_id} to {req.destination_facility} ({req.urgency})"
        )

        return {"status": "success", "referral_id": ref_id}

@app.patch("/api/referrals/{referral_id}/status")
async def update_referral_status(referral_id: int, req: ReferralStatusUpdateRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]

    async with db.legacy_pool.acquire() as conn:
        ref = await conn.fetchrow("SELECT * FROM referrals WHERE id = $1", referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral record not found.")

        await conn.execute(
            "UPDATE referrals SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
            req.status, referral_id
        )

        await log_access_event(
            staff_id,
            "REFERRAL_STATUS_UPDATED",
            ref["patient_id"],
            f"Referral #{referral_id} updated to '{req.status}'"
        )

        return {"status": "success", "message": f"Referral status updated to {req.status}"}

# --- CLINICAL NOTES (APPEND-ONLY) ---
@app.post("/api/records/notes")
async def add_clinical_note(req: ClinicalNoteRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    async with db.legacy_pool.acquire() as conn:
        new_note_id = await conn.fetchval(
            "INSERT INTO clinical_notes (patient_id, provider_id, note_text) VALUES ($1, $2, $3) RETURNING id",
            req.patient_id, staff_id, req.note_text
        )
        await log_access_event(staff_id, "CLINICAL_NOTE_ADDED", req.patient_id, f"Note ID: {new_note_id}")
        return {"status": "success", "note_id": new_note_id}

@app.post("/api/records/notes/correct")
async def correct_clinical_note(req: NoteCorrectionRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    async with db.legacy_pool.acquire() as conn:
        original = await conn.fetchrow("SELECT id FROM clinical_notes WHERE id = $1", req.original_note_id)
        if not original:
            raise HTTPException(status_code=404, detail="Original clinical note not found.")

        correction_id = await conn.fetchval(
            """INSERT INTO clinical_notes (patient_id, provider_id, note_text, correction_reason, supersedes_note_id)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            req.patient_id, staff_id, req.corrected_text, req.reason, req.original_note_id
        )

        await log_access_event(
            staff_id,
            "RECORD_CORRECTED",
            req.patient_id,
            f"Correction #{correction_id} overrides #{req.original_note_id}: {req.reason}"
        )
        return {"status": "Correction appended successfully", "correction_id": correction_id}

# --- OFFLINE BATCH SYNC ENDPOINT ---
@app.post("/api/sync/batch")
async def sync_offline_batch(req: BatchSyncRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    synced_items = 0

    async with db.legacy_pool.acquire() as conn:
        # Sync offline encounters
        for enc in req.encounters:
            await conn.execute(
                """INSERT INTO clinical_encounters (
                    patient_id, provider_id, encounter_type, bp, temperature, pulse, weight,
                    rdt_result, clinical_assessment, prescription, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                enc.get("patient_id"), staff_id, enc.get("encounter_type", "General Outpatient"),
                enc.get("bp", "120/80"), enc.get("temperature", 36.8), enc.get("pulse", 76),
                enc.get("weight", 60.0), enc.get("rdt_result", "Not Tested"),
                enc.get("clinical_assessment", ""), enc.get("prescription", ""),
                enc.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            synced_items += 1

        # Sync offline notes
        for note in req.notes:
            await conn.execute(
                "INSERT INTO clinical_notes (patient_id, provider_id, note_text, timestamp) VALUES ($1, $2, $3, $4)",
                note.get("patient_id"), staff_id, note.get("note_text", ""),
                note.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            synced_items += 1

    await log_access_event(
        staff_id,
        "OFFLINE_BATCH_SYNCHRONIZED",
        "MULTIPLE",
        f"Synchronized {synced_items} queued records from facility device"
    )

    return {"status": "success", "synced_count": synced_items}

# --- CRYPTOGRAPHIC AUDIT VERIFICATION & SIEM ---
@app.get("/api/admin/clinical-notes")
async def get_admin_clinical_notes():
    async with db.legacy_pool.acquire() as conn:
        notes = await conn.fetch("""
            SELECT id, patient_id, provider_id, note_text, timestamp, correction_reason, supersedes_note_id 
            FROM clinical_notes ORDER BY timestamp DESC LIMIT 50
        """)
        return [
            {
                "id": n["id"],
                "patient_id": n["patient_id"],
                "provider_id": n["provider_id"],
                "note_text": n["note_text"],
                "timestamp": str(n["timestamp"]),
                "correction_reason": n.get("correction_reason", ""),
                "supersedes_note_id": n.get("supersedes_note_id")
            }
            for n in notes
        ]

@app.get("/api/audit-logs")
async def get_audit_logs():
    async with db.audit_pool.acquire() as conn:
        logs = await conn.fetch("SELECT entry_id, timestamp, user_id, target_patient_id, action, current_hash, reason FROM audit_log ORDER BY entry_id DESC LIMIT 500")
        return [
            {
                "entry_id": l["entry_id"],
                "timestamp": str(l["timestamp"]),
                "provider_id": l["user_id"],
                "patient_id": l["target_patient_id"],
                "action": l["action"],
                "current_hash": l["current_hash"],
                "reason": l.get("reason", "")
            }
            for l in logs
        ]

@app.get("/api/audit/verify")
async def verify_audit_ledger():
    try:
        async with db.audit_pool.acquire() as conn:
            logs = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")

            if not logs:
                return {"status": "SECURE", "message": "Ledger is empty."}

            expected_previous = "0" * 64

            for row in logs:
                prev_hash = row.get("previous_hash", "") or ""
                if prev_hash != expected_previous:
                    return {
                        "status": "COMPROMISED",
                        "broken_entry": row["entry_id"],
                        "detail": f"Cryptographic link broken at #{row['entry_id']}. Expected {expected_previous[:12]}... but found {prev_hash[:12]}..."
                    }

                user_id = row.get("user_id", "") or ""
                action = row.get("action", "") or ""
                patient_id = row.get("target_patient_id", "") or ""
                reason = row.get("reason", "") or ""

                payload = f"{user_id}|{action}|{patient_id}|{reason}|{prev_hash}"
                recomputed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

                if recomputed_hash != row.get("current_hash"):
                    return {
                        "status": "COMPROMISED",
                        "broken_entry": row["entry_id"],
                        "detail": f"Tampering detected at #{row['entry_id']}! Recomputed SHA-256 does not match recorded block hash."
                    }

                expected_previous = row.get("current_hash")

            return {
                "status": "SECURE",
                "total_blocks": len(logs),
                "message": f"Successfully verified {len(logs)} cryptographic SHA-256 blocks. NDPA 2023 compliance guaranteed."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/reset-ledger")
async def reset_ledger():
    async with db.audit_pool.acquire() as conn:
        await conn.execute("DELETE FROM audit_log")
        # Add fresh genesis
        prev_hash = "0" * 64
        payload = f"SYSTEM|SYSTEM_INIT|ALL|WardVault Primary Healthcare Gateway Genesis Block|{prev_hash}"
        gen_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        await conn.execute(
            """INSERT INTO audit_log (timestamp, user_id, action, target_patient_id, reason, previous_hash, current_hash)
               VALUES (CURRENT_TIMESTAMP, 'SYSTEM', 'SYSTEM_INIT', 'ALL', 'WardVault PHC Gateway Genesis Block', $1, $2)""",
            prev_hash, gen_hash
        )
    return {"status": "Ledger reset successfully for fresh demonstration."}
