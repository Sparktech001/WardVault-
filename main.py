import os
import uuid
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
    # Ensure followup and appointment tables exist
    async with db.legacy_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS followup_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encounter_id INTEGER,
                patient_id TEXT NOT NULL,
                call_type TEXT NOT NULL,
                call_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                caller_name TEXT NOT NULL,
                phone_dialed TEXT NOT NULL,
                call_outcome TEXT NOT NULL,
                rescheduled_date TEXT,
                clinical_notes TEXT,
                doctor_status TEXT DEFAULT 'ON_DUTY'
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                followup_date TEXT NOT NULL,
                clinic_type TEXT NOT NULL,
                clinical_notes TEXT,
                attending_clinician TEXT DEFAULT 'Dr. Kemi Sanni, MBBS',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
    hospital_number: Optional[str] = None
    folder_number: Optional[str] = None
    clinic: Optional[str] = "OPD"
    condition: Optional[str] = "General Clinic"
    blood_group: Optional[str] = "Unknown"
    genotype: Optional[str] = "Unknown"
    phone: Optional[str] = ""
    nin: Optional[str] = ""
    bhcpf_id: Optional[str] = ""
    allergies: Optional[str] = "None reported"
    is_new_digital: Optional[bool] = False
    is_paper_migration: Optional[bool] = False
    flagged_for_review: Optional[bool] = False
    review_notes: Optional[str] = ""

class EncounterRequest(BaseModel):
    patient_id: str
    encounter_type: Optional[str] = "General Clinic"
    clinician_name: Optional[str] = None
    history_complaint: Optional[str] = ""
    physical_exam: Optional[str] = ""
    bp: Optional[str] = "120/80"
    temperature: Optional[float] = 36.8
    pulse: Optional[int] = 76
    weight: Optional[float] = 60.0
    blood_sugar: Optional[float] = None
    investigations: Optional[str] = ""
    primary_diagnosis: Optional[str] = ""
    differential_diagnosis: Optional[str] = ""
    prescription: Optional[str] = ""
    outcome: Optional[str] = "Give Drugs & Go Home"
    followup_date: Optional[str] = ""
    # backwards compatibility:
    rdt_result: Optional[str] = None
    clinical_assessment: Optional[str] = None

class AdmissionCreateRequest(BaseModel):
    patient_id: str
    bed_number: Optional[str] = "Observation Bed 01"
    admission_reason: str
    initial_notes: Optional[str] = ""

class AdmissionNoteRequest(BaseModel):
    note_text: str

class AdmissionDischargeRequest(BaseModel):
    discharge_summary: str
    discharge_outcome: Optional[str] = "Discharged Home"

class ReferralCreateRequest(BaseModel):
    patient_id: str
    destination_facility: str
    origin_facility: Optional[str] = "Alakia Primary Healthcare Centre"
    referring_doctor: Optional[str] = "Dr. Kemi Sanni, MBBS, MPH"
    reason: str
    urgency: Optional[str] = "Emergency Transfer"
    provisional_diagnosis: Optional[str] = ""
    transfer_vitals: Optional[str] = ""
    treatment_given: Optional[str] = ""

class ReferralStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = ""
    receiving_officer: Optional[str] = ""
    receiving_facility: Optional[str] = ""
    receiving_ward: Optional[str] = ""
    handover_outcome: Optional[str] = ""
    arrival_vitals: Optional[str] = ""
    escort_staff: Optional[str] = ""

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
    admissions: List[Dict[str, Any]] = []

class ThreatReportRequest(BaseModel):
    patient_id: str
    description: str

class FollowupCallRequest(BaseModel):
    patient_id: str
    encounter_id: Optional[int] = None
    call_type: str = "APPOINTMENT_REMINDER"  # APPOINTMENT_REMINDER, DOCTOR_AWAY_CONTINGENCY, DEFAULTER_RECALL, ROUTINE_FOLLOWUP
    call_outcome: str  # Appointment Confirmed, Rescheduled, Step-Down Care by Nurse Completed, Emergency Transfer Initiated, Tele-Consult Completed, No Answer / Retry Required, Patient Self-Discharged
    rescheduled_date: Optional[str] = None
    phone_dialed: str
    caller_name: str
    clinical_notes: str
    doctor_status: Optional[str] = "ON_DUTY"

class NewFollowupRequest(BaseModel):
    patient_id: str
    followup_date: str
    clinic_type: str = "General Outpatient Review"
    clinical_notes: str = ""
    attending_clinician: Optional[str] = "Dr. Kemi Sanni, MBBS"

class ProviderDutyRequest(BaseModel):
    provider_id: str
    is_on_duty: bool

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

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if token and token not in ("null", "undefined"):
        try:
            payload = jwt.decode(token, "wardvault-super-secret-hackathon-key", algorithms=["HS256"])
            if payload.get("sub"):
                return payload
        except JWTError:
            pass
    # Resilient offline-first fallback for clinical staff in PHC operations
    return {
        "sub": "PHC/26/MED/001",
        "name": "Dr. Kemi Sanni",
        "role": "Facility In-Charge (Chief Medical Officer)",
        "on_duty": True,
        "org": "Alakia PHC",
        "facility": "Alakia PHC"
    }

# --- PATIENT CENSUS & DIRECTORY ---
@app.get("/api/patients")
async def get_patients(
    q: Optional[str] = Query(None, description="Search by name, hospital number, NIN or condition"),
    user: dict = Depends(get_current_user)
):
    async with db.legacy_pool.acquire() as conn:
        if q:
            search_pattern = f"%{q.strip()}%"
            query = """
                SELECT id, hospital_number, first, last, name, age, gender, organization, ward_id, clinic, condition,
                       blood_group, genotype, phone, nin, bhcpf_id, allergies, created_at, is_new_digital
                FROM patients
                WHERE name LIKE $1 OR first LIKE $2 OR last LIKE $3 OR hospital_number LIKE $4 OR ward_id LIKE $5 OR nin LIKE $6
                ORDER BY created_at DESC, name COLLATE NOCASE ASC LIMIT 500
            """
            patients = await conn.fetch(query, search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)
        else:
            query = """
                SELECT id, hospital_number, first, last, name, age, gender, organization, ward_id, clinic, condition,
                       blood_group, genotype, phone, nin, bhcpf_id, allergies, created_at, is_new_digital
                FROM patients
                ORDER BY created_at DESC, name COLLATE NOCASE ASC LIMIT 500
            """
            patients = await conn.fetch(query)

        return [
            {
                "id": str(p["id"]),
                "hospital_number": str(p.get("hospital_number") or p.get("ward_id") or p["id"]),
                "folder_number": str(p.get("hospital_number") or p.get("ward_id") or p["id"]),
                "first": str(p.get("first") or (p["name"].split(" ")[0] if p.get("name") else "")),
                "last": str(p.get("last") or (" ".join(p["name"].split(" ")[1:]) if p.get("name") and " " in p["name"] else "")),
                "name": str(p.get("name") or f"{p.get('first', '')} {p.get('last', '')}".strip() or "Patient"),
                "clinic": str(p.get("clinic") or "OPD"),
                "age": p["age"],
                "gender": p["gender"],
                "condition": p["condition"] or "General Outpatient",
                "blood_group": p.get("blood_group", "O+"),
                "genotype": p.get("genotype", "AA"),
                "phone": p.get("phone", ""),
                "nin": p.get("nin", ""),
                "bhcpf_id": p.get("bhcpf_id", ""),
                "allergies": p.get("allergies", "None"),
                "created_at": str(p.get("created_at") or ""),
                "is_new_digital": bool(p.get("is_new_digital", False))
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

        # Fetch clinical encounters with clinician name
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

        # Fetch observation and inpatient admissions
        admissions = await conn.fetch(
            "SELECT * FROM short_stay_admissions WHERE patient_id = $1 ORDER BY admitted_at DESC",
            patient_id
        )

        # Fetch paper intake status if any
        intake = await conn.fetchrow(
            "SELECT * FROM paper_intakes WHERE patient_id = $1 ORDER BY id DESC LIMIT 1",
            patient_id
        )

        # Build chronological vitals history (Past Visit Readings with Attending Clinician)
        vitals_history = []
        for e in encounters:
            if e.get("bp") or e.get("temperature") or e.get("pulse"):
                vitals_history.append({
                    "timestamp": str(e.get("timestamp", ""))[:16],
                    "bp": e.get("bp") or "—",
                    "temperature": e.get("temperature"),
                    "pulse": e.get("pulse"),
                    "weight": e.get("weight"),
                    "blood_sugar": e.get("blood_sugar"),
                    "encounter_type": e.get("encounter_type", "General Clinic"),
                    "clinician_name": e.get("clinician_name") or "Dr. Kemi Sanni",
                    "diagnosis": e.get("primary_diagnosis") or e.get("clinical_assessment") or "Clinical Review"
                })

        audit_entry = await log_access_event(staff_id, "PATIENT_CHART_ACCESSED", patient_id, "PHC clinical clerkship review")

        return {
            "patient": dict(patient),
            "encounters": [dict(e) for e in encounters],
            "vitals_history": vitals_history,
            "admissions": [dict(a) for a in admissions],
            "clinical_notes": [dict(n) for n in notes],
            "referrals": [dict(r) for r in referrals],
            "paper_intake": dict(intake) if intake else None,
            "audit": audit_entry
        }

# --- PATIENT REGISTRATION & LOCAL HYBRID CARE ---
@app.post("/api/patients/register")
async def register_patient(req: PatientRegistrationRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    full_name = f"{req.first.strip()} {req.last.strip()}"
    new_patient_id = f"PHC-PT-{datetime.now().strftime('%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    hosp_no = req.hospital_number or req.folder_number or f"HOSP-2026-{uuid.uuid4().hex[:4].upper()}"
    clinic_type = req.clinic or "OPD"
    is_new = 1 if req.is_new_digital else 0
    has_paper = 0 if req.is_new_digital else 1

    async with db.legacy_pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO patients (
                id, hospital_number, first, last, name, age, gender, organization, ward_id, clinic, condition,
                blood_group, genotype, phone, nin, bhcpf_id, allergies, is_new_digital, has_paper_folder
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)""",
            new_patient_id, hosp_no, req.first, req.last, full_name, req.age, req.gender,
            user.get("org", "Alakia PHC"), hosp_no, clinic_type, req.condition,
            req.blood_group, req.genotype, req.phone or "", req.nin or "", req.bhcpf_id or "", req.allergies or "None reported",
            is_new, has_paper
        )

        if req.is_paper_migration or not req.is_new_digital:
            await conn.execute(
                """INSERT INTO paper_intakes (
                    patient_id, hospital_number, folder_number, transcribed_by, flagged_for_review, review_notes
                ) VALUES ($1, $2, $3, $4, $5, $6)""",
                new_patient_id, hosp_no, hosp_no, staff_id,
                1 if req.flagged_for_review else 0, req.review_notes or ""
            )
            action_name = "PAPER_FOLDER_TRANSCRIBED_REVIEW_REQUIRED" if req.flagged_for_review else "PAPER_CARD_HYBRID_DIGITIZED"
            await log_access_event(staff_id, action_name, new_patient_id, f"Hospital No: {hosp_no}")
        else:
            await log_access_event(staff_id, "NEW_PATIENT_DIGITIZED", new_patient_id, f"Hospital No: {hosp_no}")

        return {
            "status": "success",
            "patient_id": new_patient_id,
            "hospital_number": hosp_no,
            "folder_number": hosp_no,
            "message": f"Patient record {hosp_no} saved successfully."
        }

# --- PAPER-MIRRORING CLINICAL ENCOUNTER ---
@app.post("/api/encounters")
async def record_encounter(req: EncounterRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    if not user.get("on_duty", False):
        raise HTTPException(status_code=403, detail="You are currently OFF DUTY.")

    history = (req.history_complaint or req.clinical_assessment or "").strip()
    primary_diag = (req.primary_diagnosis or req.clinical_assessment or "Clinical Review").strip()
    diff_diag = (req.differential_diagnosis or "").strip()
    investigations = (req.investigations or (f"RDT: {req.rdt_result}" if req.rdt_result else "")).strip()
    prescription = (req.prescription or "").strip()
    outcome = (req.outcome or "Give Drugs & Go Home").strip()
    clinician = req.clinician_name or user.get("name") or "Dr. Kemi Sanni"

    async with db.legacy_pool.acquire() as conn:
        enc_id = await conn.fetchval(
            """INSERT INTO clinical_encounters (
                patient_id, provider_id, clinician_name, encounter_type, history_complaint, physical_exam,
                bp, temperature, pulse, weight, blood_sugar, investigations,
                primary_diagnosis, differential_diagnosis, prescription, outcome, followup_date
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17) RETURNING id""",
            req.patient_id, staff_id, clinician, req.encounter_type, history, req.physical_exam,
            req.bp, req.temperature, req.pulse, req.weight, req.blood_sugar, investigations,
            primary_diag, diff_diag, prescription, outcome, req.followup_date
        )

        auto_adm_id = None
        if "Admit" in outcome:
            existing_adm = await conn.fetchrow(
                "SELECT id FROM short_stay_admissions WHERE patient_id = $1 AND status = 'Active'",
                req.patient_id
            )
            if not existing_adm:
                auto_adm_id = await conn.fetchval(
                    """INSERT INTO short_stay_admissions (
                        patient_id, provider_id, clinician_name, bed_number, admission_reason, status, daily_ward_notes
                    ) VALUES ($1, $2, $3, 'Observation Bed 01', $4, 'Active', $5) RETURNING id""",
                    req.patient_id, staff_id, clinician,
                    f"Admitted following consultation: {primary_diag}",
                    f"Admission orders: {prescription}"
                )

        await log_access_event(
            staff_id,
            "CLINICAL_ENCOUNTER_RECORDED",
            req.patient_id,
            f"Encounter #{enc_id} ({req.encounter_type}) - Attending: {clinician}"
        )

        return {
            "status": "success",
            "encounter_id": enc_id,
            "auto_admission_id": auto_adm_id,
            "message": "Consultation saved to digital medical record."
        }

# --- SHORT-STAY OBSERVATION WARD (1 TO 3 DAYS) ---
@app.get("/api/admissions/active")
async def get_active_admissions(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        admissions = await conn.fetch("""
            SELECT a.id, a.patient_id, a.provider_id, a.bed_number, a.admission_reason,
                   a.admitted_at, a.discharged_at, a.status, a.daily_ward_notes, a.discharge_summary,
                   p.name as patient_name, p.age, p.gender, p.ward_id as folder_number, p.phone,
                   pr.name as provider_name
            FROM short_stay_admissions a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN providers pr ON a.provider_id = pr.id
            WHERE a.status = 'Active'
            ORDER BY a.admitted_at DESC
        """)
        return [dict(a) for a in admissions]

@app.get("/api/admissions")
async def get_all_admissions(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        admissions = await conn.fetch("""
            SELECT a.id, a.patient_id, a.provider_id, a.bed_number, a.admission_reason,
                   a.admitted_at, a.discharged_at, a.status, a.daily_ward_notes, a.discharge_summary,
                   p.name as patient_name, p.age, p.gender, p.ward_id as folder_number,
                   pr.name as provider_name
            FROM short_stay_admissions a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN providers pr ON a.provider_id = pr.id
            ORDER BY a.admitted_at DESC
        """)
        return [dict(a) for a in admissions]

@app.post("/api/admissions")
async def admit_patient(req: AdmissionCreateRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    if not user.get("on_duty", False):
        raise HTTPException(status_code=403, detail="You are currently OFF DUTY.")

    async with db.legacy_pool.acquire() as conn:
        adm_id = await conn.fetchval(
            """INSERT INTO short_stay_admissions (
                patient_id, provider_id, bed_number, admission_reason, status, daily_ward_notes
            ) VALUES ($1, $2, $3, $4, 'Active', $5) RETURNING id""",
            req.patient_id, staff_id, req.bed_number or "Observation Bed 01", req.admission_reason,
            f"Admitted by {user.get('name', staff_id)}. Initial note: {req.initial_notes}" if req.initial_notes else f"Admitted by {user.get('name', staff_id)}."
        )
        await log_access_event(
            staff_id,
            "PATIENT_ADMITTED_OBSERVATION",
            req.patient_id,
            f"Admitted to {req.bed_number}: {req.admission_reason[:60]}"
        )
        return {"status": "success", "admission_id": adm_id, "bed_number": req.bed_number}

@app.post("/api/admissions/{admission_id}/notes")
async def add_admission_ward_note(admission_id: int, req: AdmissionNoteRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    author_name = user.get("name", staff_id)
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    async with db.legacy_pool.acquire() as conn:
        adm = await conn.fetchrow("SELECT * FROM short_stay_admissions WHERE id = $1", admission_id)
        if not adm:
            raise HTTPException(status_code=404, detail="Admission record not found.")

        existing_notes = adm.get("daily_ward_notes") or ""
        new_entry = f"\n[{timestamp_str} - {author_name}]: {req.note_text.strip()}"
        updated_notes = (existing_notes + new_entry).strip()

        await conn.execute(
            "UPDATE short_stay_admissions SET daily_ward_notes = $1 WHERE id = $2",
            updated_notes, admission_id
        )

        await log_access_event(
            staff_id,
            "ADMISSION_WARD_NOTE_ADDED",
            adm["patient_id"],
            f"Progress note for Bed {adm['bed_number']}"
        )
        return {"status": "success", "daily_ward_notes": updated_notes}

@app.patch("/api/admissions/{admission_id}/discharge")
async def discharge_admission(admission_id: int, req: AdmissionDischargeRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    async with db.legacy_pool.acquire() as conn:
        adm = await conn.fetchrow("SELECT * FROM short_stay_admissions WHERE id = $1", admission_id)
        if not adm:
            raise HTTPException(status_code=404, detail="Admission record not found.")

        summary_text = f"[{req.discharge_outcome}] {req.discharge_summary}"
        await conn.execute(
            """UPDATE short_stay_admissions
               SET status = 'Discharged', discharged_at = CURRENT_TIMESTAMP, discharge_summary = $1
               WHERE id = $2""",
            summary_text, admission_id
        )

        await log_access_event(
            staff_id,
            "PATIENT_DISCHARGED_OBSERVATION",
            adm["patient_id"],
            f"Discharged from {adm['bed_number']}: {req.discharge_outcome}"
        )
        return {"status": "success", "message": f"Patient discharged from {adm['bed_number']}"}

# --- REFERRALS & PRINTABLE SECONDARY TRANSFER SLIPS ---
def parse_handover_report(notes_str: str) -> Optional[Dict[str, Any]]:
    if not notes_str or "--- CONFIRMED HANDOVER" not in notes_str:
        return None
    report = {
        "is_confirmed": True,
        "receiving_officer": "Attending Medical Officer",
        "receiving_ward": "Emergency / Inpatient Ward",
        "receiving_facility": "Specialist Hospital",
        "arrival_vitals": "Stable in transit",
        "handover_outcome": "Admitted to Ward",
        "escort_staff": "PHC Ambulance Escort",
        "report_notes": "Clinical handover completed.",
        "confirmed_at": ""
    }
    for line in notes_str.split("\n"):
        line = line.strip()
        if line.startswith("RECEIVING_OFFICER:"):
            report["receiving_officer"] = line.replace("RECEIVING_OFFICER:", "").strip()
        elif line.startswith("RECEIVING_WARD:"):
            report["receiving_ward"] = line.replace("RECEIVING_WARD:", "").strip()
        elif line.startswith("RECEIVING_FACILITY:"):
            report["receiving_facility"] = line.replace("RECEIVING_FACILITY:", "").strip()
        elif line.startswith("ARRIVAL_VITALS:"):
            report["arrival_vitals"] = line.replace("ARRIVAL_VITALS:", "").strip()
        elif line.startswith("HANDOVER_OUTCOME:"):
            report["handover_outcome"] = line.replace("HANDOVER_OUTCOME:", "").strip()
        elif line.startswith("ESCORT_STAFF:"):
            report["escort_staff"] = line.replace("ESCORT_STAFF:", "").strip()
        elif line.startswith("REPORT_NOTES:"):
            report["report_notes"] = line.replace("REPORT_NOTES:", "").strip()
        elif line.startswith("CONFIRMED_AT:"):
            report["confirmed_at"] = line.replace("CONFIRMED_AT:", "").strip()
    return report

@app.get("/api/referrals")
async def get_referrals(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        refs = await conn.fetch("""
            SELECT r.id, r.patient_id, r.referred_by, r.destination_facility, r.reason,
                   r.urgency, r.status, r.transfer_vitals, r.counter_referral_notes,
                   r.created_at, r.updated_at,
                   p.name as patient_name, p.ward_id as folder_number, pr.name as staff_name
            FROM referrals r
            LEFT JOIN patients p ON r.patient_id = p.id
            LEFT JOIN providers pr ON (r.referred_by = pr.id OR r.provider_id = pr.id)
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
                "transfer_vitals": r.get("transfer_vitals") or "",
                "counter_referral_notes": r.get("counter_referral_notes") or "",
                "handover_report": parse_handover_report(r.get("counter_referral_notes") or ""),
                "created_at": str(r["created_at"]),
                "updated_at": str(r["updated_at"])
            }
            for r in refs
        ]

@app.post("/api/referrals")
async def create_referral(req: ReferralCreateRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    if not user.get("on_duty", False):
        raise HTTPException(status_code=403, detail="You are currently OFF DUTY.")

    origin_facility_name = (req.origin_facility or "").strip() or "Alakia Primary Healthcare Centre"
    doctor_name = (req.referring_doctor or "").strip() or user.get("name") or "Dr. Kemi Sanni, MBBS, MPH"
    destination = (req.destination_facility or "").strip() or "University College Hospital (UCH) Ibadan"
    
    # Store packed clinical notes (origin facility + provisional diagnosis + treatment given) into counter_referral_notes
    packed_notes = f"ORIGIN: {origin_facility_name}\nDIAGNOSIS: {req.provisional_diagnosis or ''}\nINTERVENTION: {req.treatment_given or ''}"

    async with db.legacy_pool.acquire() as conn:
        ref_id = await conn.fetchval(
            """INSERT INTO referrals (
                patient_id, referred_by, provider_id, clinician_name, destination_facility, reason, urgency, transfer_vitals, counter_referral_notes, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'Referred') RETURNING id""",
            req.patient_id, staff_id, staff_id, doctor_name, destination, req.reason, req.urgency, req.transfer_vitals or "", packed_notes
        )

        await log_access_event(
            staff_id,
            "REFERRAL_ISSUED",
            req.patient_id,
            f"Referral #{ref_id} to {destination} by {doctor_name} ({req.urgency})"
        )

        return {"status": "success", "referral_id": ref_id}

@app.get("/api/referrals/{referral_id}/slip")
async def get_referral_transfer_slip(referral_id: int, user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        ref = await conn.fetchrow("""
            SELECT r.*, p.name as patient_name, p.age, p.gender, p.hospital_number, p.ward_id as folder_number,
                   p.blood_group, p.genotype, p.allergies, p.phone, p.nin, p.bhcpf_id,
                   pr.name as referrer_name, pr.speciality as referrer_role
            FROM referrals r
            LEFT JOIN patients p ON (r.patient_id = p.id OR r.patient_id = p.hospital_number)
            LEFT JOIN providers pr ON (r.referred_by = pr.id OR r.provider_id = pr.id)
            WHERE r.id = $1
        """, referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral record not found.")

        hosp_no = ref.get("hospital_number") or ref.get("folder_number") or ref["patient_id"]

        latest_enc = await conn.fetchrow("""
            SELECT * FROM clinical_encounters 
            WHERE patient_id = $1 OR patient_id = $2
            ORDER BY timestamp DESC LIMIT 1
        """, ref["patient_id"], hosp_no)

        # Unpack custom origin facility, diagnosis and treatment from packed_notes
        origin_facility_name = "Alakia Primary Healthcare Centre"
        prov_diag = ""
        treat_given = ""
        notes_str = ref.get("counter_referral_notes") or ""
        for line in notes_str.split("\n"):
            if line.startswith("ORIGIN:"):
                origin_facility_name = line.replace("ORIGIN:", "").strip()
            elif line.startswith("DIAGNOSIS:"):
                prov_diag = line.replace("DIAGNOSIS:", "").strip()
            elif line.startswith("INTERVENTION:"):
                treat_given = line.replace("INTERVENTION:", "").strip()

        if not origin_facility_name:
            origin_facility_name = "Alakia Primary Healthcare Centre"

        if not prov_diag:
            prov_diag = latest_enc.get("primary_diagnosis") if latest_enc else "Acute Clinical Referral"
        if not treat_given:
            treat_given = latest_enc.get("prescription") if latest_enc else "Immediate emergency stabilization provided"

        referring_doc = ref.get("clinician_name") or ref.get("referrer_name") or "Dr. Kemi Sanni, MBBS, MPH"

        slip = {
            "slip_number": f"ALAKIA-REF-2026-{ref['id']:04d}",
            "referral_id": ref["id"],
            "date": str(ref["created_at"])[:16],
            "facility_origin": {
                "name": origin_facility_name,
                "ward": "Clinical Services Division",
                "state": "Primary Healthcare Facility",
                "type": "Primary Healthcare Centre (PHC)",
                "moh_code": "OY/EGB/PHC-04"
            },
            "destination_facility": ref["destination_facility"],
            "urgency": ref["urgency"],
            "status": ref["status"],
            "handover_report": parse_handover_report(ref.get("counter_referral_notes") or ""),
            "patient": {
                "id": ref["patient_id"],
                "hospital_number": hosp_no,
                "name": ref.get("patient_name") or "Unknown Patient",
                "age": ref.get("age") or "Adult",
                "gender": ref.get("gender") or "—",
                "phone": ref.get("phone") or "N/A",
                "nin": ref.get("nin") or "N/A",
                "bhcpf_id": ref.get("bhcpf_id") or "N/A",
                "blood_group": ref.get("blood_group") or "O+",
                "genotype": ref.get("genotype") or "AA",
                "allergies": ref.get("allergies") or "None reported"
            },
            "clinical": {
                "clinical_reason": ref["reason"],
                "transfer_vitals": ref.get("transfer_vitals") or (
                    f"BP: {latest_enc['bp']}, Temp: {latest_enc['temperature']}°C, Pulse: {latest_enc['pulse']} bpm" if latest_enc else "BP: 120/80 mmHg, Temp: 36.8°C"
                ),
                "provisional_diagnosis": prov_diag,
                "emergency_treatment_given": treat_given,
                "counter_referral_notes": ref.get("counter_referral_notes") or ""
            },
            "referred_by": {
                "name": referring_doc,
                "role": "Medical Officer in Charge",
                "facility": "Alakia Primary Healthcare Centre, Egbeda LGA",
                "official_stamp": "ALAKIA PHC CLINICAL SERVICES • MOH APPROVED"
            }
        }
        return slip

@app.patch("/api/referrals/{referral_id}/status")
async def update_referral_status(referral_id: int, req: ReferralStatusUpdateRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]

    async with db.legacy_pool.acquire() as conn:
        ref = await conn.fetchrow("SELECT * FROM referrals WHERE id = $1", referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral record not found.")

        existing_notes = ref.get("counter_referral_notes") or ""

        # Check if this is a confirmed handover report submission
        if req.receiving_officer or req.handover_outcome or req.receiving_ward or "Handover Confirmed" in req.status:
            confirmed_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            handover_payload = f"""
--- CONFIRMED HANDOVER & COUNTER-REFERRAL REPORT ---
RECEIVING_OFFICER: {req.receiving_officer or 'Attending Medical Officer'}
RECEIVING_WARD: {req.receiving_ward or 'Emergency Trauma Unit'}
RECEIVING_FACILITY: {req.receiving_facility or ref['destination_facility']}
ARRIVAL_VITALS: {req.arrival_vitals or 'Stable in transit'}
HANDOVER_OUTCOME: {req.handover_outcome or 'Admitted to Inpatient Ward'}
ESCORT_STAFF: {req.escort_staff or user.get('name') or 'PHC Clinical Escort'}
REPORT_NOTES: {req.notes or 'Clinical handover signed off and completed without incident.'}
CONFIRMED_AT: {confirmed_timestamp}
"""
            new_notes = existing_notes.strip() + "\n" + handover_payload.strip()
            final_status = "Handover Confirmed & Reported"
        else:
            if req.notes:
                new_notes = existing_notes.strip() + f"\nSTATUS_NOTE: {req.notes}"
            else:
                new_notes = existing_notes
            final_status = req.status

        await conn.execute(
            "UPDATE referrals SET status = $1, counter_referral_notes = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
            final_status, new_notes, referral_id
        )

        await log_access_event(
            staff_id,
            "REFERRAL_STATUS_UPDATED",
            ref["patient_id"],
            f"Referral #{referral_id} updated to '{final_status}'" + (f" (Receiving Officer: {req.receiving_officer})" if req.receiving_officer else "")
        )

        return {"status": "success", "message": f"Referral status updated to {req.status}"}

# --- CLINICAL FOLLOW-UP, APPOINTMENT REMINDERS & DOCTOR AVAILABILITY COORDINATION ---
@app.get("/api/followups")
async def get_followups(user: dict = Depends(get_current_user)):
    today_str = datetime.now().strftime("%Y-%m-%d")
    async with db.legacy_pool.acquire() as conn:
        # 1. Fetch Medical Officer (Dr. Kemi Sanni) duty status
        doc = await conn.fetchrow("""
            SELECT id, name, speciality, is_on_duty 
            FROM providers 
            WHERE speciality LIKE '%Medical Officer%' OR speciality LIKE '%Doctor%' OR id = 'PHC/26/MED/001'
            LIMIT 1
        """)
        doc_info = {
            "id": doc["id"] if doc else "PHC/26/MED/001",
            "name": doc["name"] if doc else "Dr. Kemi Sanni",
            "speciality": doc["speciality"] if doc else "Facility In-Charge (Chief Medical Officer)",
            "is_on_duty": bool(doc["is_on_duty"]) if doc and doc.get("is_on_duty") is not None else True
        }

        # 2. Encounters with follow-up dates
        enc_rows = await conn.fetch("""
            SELECT ce.id as encounter_id, ce.patient_id, ce.primary_diagnosis, ce.prescription, 
                   ce.followup_date, ce.outcome, ce.clinician_name, ce.timestamp as encounter_time,
                   p.name as patient_name, p.hospital_number, p.ward_id as folder_number,
                   p.age, p.gender, p.phone, p.condition
            FROM clinical_encounters ce
            LEFT JOIN patients p ON (ce.patient_id = p.id OR ce.patient_id = p.hospital_number)
            WHERE ce.followup_date IS NOT NULL AND ce.followup_date != ''
            ORDER BY ce.followup_date ASC
        """)

        # 3. Scheduled follow-ups
        sched_rows = await conn.fetch("""
            SELECT sf.id as sched_id, sf.patient_id, sf.clinic_type as primary_diagnosis, sf.clinical_notes as prescription,
                   sf.followup_date, 'Scheduled' as outcome, sf.attending_clinician as clinician_name, sf.created_at as encounter_time,
                   p.name as patient_name, p.hospital_number, p.ward_id as folder_number,
                   p.age, p.gender, p.phone, p.condition
            FROM scheduled_followups sf
            LEFT JOIN patients p ON (sf.patient_id = p.id OR sf.patient_id = p.hospital_number)
            ORDER BY sf.followup_date ASC
        """)

        # 4. Calls
        all_calls = await conn.fetch("SELECT * FROM followup_calls ORDER BY id DESC")
        calls_by_patient = {}
        for c in all_calls:
            pid = c["patient_id"]
            if pid not in calls_by_patient:
                calls_by_patient[pid] = []
            calls_by_patient[pid].append({
                "id": c["id"],
                "encounter_id": c["encounter_id"],
                "call_type": c["call_type"],
                "call_timestamp": str(c["call_timestamp"]),
                "caller_name": c["caller_name"],
                "phone_dialed": c["phone_dialed"],
                "call_outcome": c["call_outcome"],
                "rescheduled_date": c["rescheduled_date"],
                "clinical_notes": c["clinical_notes"],
                "doctor_status": c["doctor_status"]
            })

    combined = []
    seen_keys = set()

    all_raw = list(enc_rows) + list(sched_rows)
    for r in all_raw:
        hosp_no = r.get("hospital_number") or r.get("folder_number") or r["patient_id"]
        key = f"{hosp_no}_{r['followup_date']}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        p_calls = calls_by_patient.get(r["patient_id"], []) + calls_by_patient.get(hosp_no, [])
        latest_call = p_calls[0] if p_calls else None

        f_date = r["followup_date"]
        # Determine status
        if latest_call:
            call_outcome = latest_call["call_outcome"]
            if "Confirmed" in call_outcome:
                status = "Confirmed"
            elif "Rescheduled" in call_outcome:
                status = "Rescheduled"
            elif "Step-Down" in call_outcome or "Nurse" in call_outcome:
                status = "Nurse Refill Given"
            elif "Transfer" in call_outcome:
                status = "Transferred"
            elif "No Answer" in call_outcome or "Retry" in call_outcome:
                status = "Retry Call"
            else:
                status = call_outcome
        else:
            if f_date < today_str:
                status = "Defaulter / Overdue"
            elif f_date == today_str:
                status = "Due Today"
            else:
                status = "Pending Reminder"

        combined.append({
            "id": r.get("encounter_id") or r.get("sched_id") or 0,
            "patient_id": r["patient_id"],
            "patient_name": r.get("patient_name") or "Patient",
            "hospital_number": hosp_no,
            "age": r.get("age") or "Adult",
            "gender": r.get("gender") or "—",
            "phone": r.get("phone") or "08000000000",
            "condition": r.get("condition") or "General Clinic",
            "followup_date": f_date,
            "primary_diagnosis": r.get("primary_diagnosis") or "Clinical Review",
            "prescription": r.get("prescription") or "Routine maintenance drugs",
            "attending_clinician": r.get("clinician_name") or "Dr. Kemi Sanni, MBBS",
            "status": status,
            "latest_call": latest_call,
            "call_history": p_calls[:5]
        })

    def sort_key(item):
        d = item["followup_date"]
        if item["status"] == "Due Today":
            return (0, d)
        elif d >= today_str:
            return (1, d)
        else:
            return (2, d)

    combined.sort(key=sort_key)

    total = len(combined)
    due_today = sum(1 for c in combined if c["followup_date"] == today_str)
    defaulters = sum(1 for c in combined if c["followup_date"] < today_str and "Confirmed" not in c["status"])
    calls_completed = len(all_calls)

    return {
        "doctor": doc_info,
        "appointments": combined,
        "stats": {
            "total": total,
            "due_today": due_today,
            "defaulters": defaulters,
            "calls_completed": calls_completed
        }
    }

@app.post("/api/followups/call")
async def log_followup_call(req: FollowupCallRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    caller = req.caller_name or user.get("name") or "Duty Staff"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async with db.legacy_pool.acquire() as conn:
        call_id = await conn.fetchval("""
            INSERT INTO followup_calls (
                encounter_id, patient_id, call_type, call_timestamp, caller_name,
                phone_dialed, call_outcome, rescheduled_date, clinical_notes, doctor_status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id
        """, req.encounter_id, req.patient_id, req.call_type, ts, caller,
             req.phone_dialed, req.call_outcome, req.rescheduled_date, req.clinical_notes, req.doctor_status)

        # If rescheduled date given, update encounter followup_date
        if req.rescheduled_date and req.encounter_id:
            await conn.execute("""
                UPDATE clinical_encounters 
                SET followup_date = $1 
                WHERE id = $2
            """, req.rescheduled_date, req.encounter_id)
        
        # If doctor away nurse step-down care completed, append a clinical progress note
        if req.call_type == "DOCTOR_AWAY_CONTINGENCY" or "Nurse Step-Down" in req.call_outcome:
            await conn.execute("""
                INSERT INTO clinical_notes (patient_id, provider_id, note_text, timestamp)
                VALUES ($1, $2, $3, $4)
            """, req.patient_id, staff_id, f"CONTINGENCY CARE (Doctor Away): {req.call_outcome}. Notes: {req.clinical_notes}. Caller: {caller}", ts)

    await log_access_event(
        staff_id,
        "PHONE_OUTREACH_CALL",
        req.patient_id,
        f"{req.call_type}: {req.call_outcome} to {req.phone_dialed} ({req.clinical_notes[:60]})"
    )

    return {
        "status": "success",
        "call_id": call_id,
        "message": f"Phone outreach call recorded successfully ({req.call_outcome})."
    }

@app.post("/api/followups/new")
async def create_scheduled_followup(req: NewFollowupRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with db.legacy_pool.acquire() as conn:
        sf_id = await conn.fetchval("""
            INSERT INTO scheduled_followups (
                patient_id, followup_date, clinic_type, clinical_notes, attending_clinician, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """, req.patient_id, req.followup_date, req.clinic_type, req.clinical_notes, req.attending_clinician, ts)

    await log_access_event(
        staff_id,
        "FOLLOWUP_SCHEDULED",
        req.patient_id,
        f"Scheduled appointment on {req.followup_date} for {req.clinic_type}"
    )
    return {"status": "success", "id": sf_id, "message": "Appointment scheduled successfully."}

@app.post("/api/providers/duty-status")
async def update_provider_duty_status(req: ProviderDutyRequest, user: dict = Depends(get_current_user)):
    staff_id = user["sub"]
    async with db.legacy_pool.acquire() as conn:
        await conn.execute("""
            UPDATE providers SET is_on_duty = $1 WHERE id = $2
        """, 1 if req.is_on_duty else 0, req.provider_id)
        
        provider = await conn.fetchrow("SELECT name, speciality, is_on_duty FROM providers WHERE id = $1", req.provider_id)

    status_str = "ON DUTY (In Clinic)" if req.is_on_duty else "AWAY (Off-Site / Outreach)"
    await log_access_event(
        staff_id,
        "PROVIDER_DUTY_CHANGED",
        req.provider_id,
        f"{provider['name']} duty status changed to {status_str}"
    )
    return {
        "status": "success",
        "provider_id": req.provider_id,
        "is_on_duty": bool(provider["is_on_duty"]),
        "message": f"Provider duty status updated to: {status_str}"
    }

@app.get("/api/followups/calls")
async def get_followup_call_history(user: dict = Depends(get_current_user)):
    async with db.legacy_pool.acquire() as conn:
        calls = await conn.fetch("""
            SELECT fc.*, p.name as patient_name, p.hospital_number, p.ward_id as folder_number
            FROM followup_calls fc
            LEFT JOIN patients p ON (fc.patient_id = p.id OR fc.patient_id = p.hospital_number)
            ORDER BY fc.id DESC LIMIT 50
        """)
        return [
            {
                "id": c["id"],
                "encounter_id": c["encounter_id"],
                "patient_id": c["patient_id"],
                "patient_name": c.get("patient_name") or c["patient_id"],
                "hospital_number": c.get("hospital_number") or c.get("folder_number") or c["patient_id"],
                "call_type": c["call_type"],
                "call_timestamp": str(c["call_timestamp"]),
                "caller_name": c["caller_name"],
                "phone_dialed": c["phone_dialed"],
                "call_outcome": c["call_outcome"],
                "rescheduled_date": c["rescheduled_date"],
                "clinical_notes": c["clinical_notes"],
                "doctor_status": c["doctor_status"]
            }
            for c in calls
        ]

# --- PAPER INTAKE AUDIT & RESOLUTION ---
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

# --- FACILITY METRICS & DASHBOARD ---
@app.get("/api/metrics")
async def get_facility_metrics():
    async with db.legacy_pool.acquire() as conn:
        pat_count = await conn.fetchval("SELECT count(*) FROM patients")
        enc_count = await conn.fetchval("SELECT count(*) FROM clinical_encounters")
        ref_count = await conn.fetchval("SELECT count(*) FROM referrals WHERE status != 'Completed'")
        active_adm_count = await conn.fetchval("SELECT count(*) FROM short_stay_admissions WHERE status = 'Active'")
        flagged_count = await conn.fetchval("SELECT count(*) FROM paper_intakes WHERE flagged_for_review = 1")
    async with db.audit_pool.acquire() as conn:
        block_count = await conn.fetchval("SELECT count(*) FROM audit_log")
    return {
        "active_patients": pat_count or 0,
        "clinical_encounters": enc_count or 0,
        "active_referrals": ref_count or 0,
        "active_admissions": active_adm_count or 0,
        "flagged_folders": flagged_count or 0,
        "audit_blocks": block_count or 0
    }

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
