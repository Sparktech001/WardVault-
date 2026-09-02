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

# The updated request body (user_id is removed because we use the JWT token now)
class RecordAccessRequest(BaseModel):
    patient_id: str
    client_ward_id: str
    is_emergency: bool = False
    override_reason: str = None

@app.get("/health")
async def health_check():
    return {"status": "online", "system": "WardVault Gateway"}

# --- 1. THE NEW LOGIN ENDPOINT ---
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with db.legacy_pool.acquire() as conn:
        # form_data.username is whatever they type into the ID field on the frontend
        user = await conn.fetchrow(
            "SELECT id, password_hash, speciality FROM providers WHERE id = $1", 
            form_data.username
        )
        
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect ID or password")
        
        # Give them a temporary access pass (JWT)
        access_token = create_access_token(
            data={"sub": user["id"], "role": user["speciality"]}
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

# --- 3. THE SECURE ACCESS ROUTE ---
@app.post("/api/records/access")
async def access_patient_record(
    req: RecordAccessRequest, 
    current_user_id: str = Depends(get_current_user_id) # <--- Demands a valid token!
):
    async with db.legacy_pool.acquire() as conn:
        staff = await conn.fetchrow(
            "SELECT p.id, p.speciality, s.ward_id, s.is_active FROM providers p LEFT JOIN active_shifts s ON p.id = s.provider_id WHERE p.id = $1",
            current_user_id
        )
        if not staff:
            raise HTTPException(status_code=404, detail="Provider not found")

        is_authorized = (staff["is_active"] is True and staff["ward_id"] == req.client_ward_id)

        if not is_authorized and req.is_emergency:
            if staff["speciality"] == "Billing Clerk":
                await log_access_event(current_user_id, "UNAUTHORIZED_OVERRIDE_ATTEMPT", req.patient_id, "Clerk attempted override")
                raise HTTPException(status_code=403, detail="Emergency override denied: non-clinical role.")
            
            audit_entry = await log_access_event(current_user_id, "EMERGENCY_OVERRIDE_GRANTED", req.patient_id, req.override_reason)
            patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", req.patient_id)
            
            if not patient: # <--- NEW CHECK HERE: Stops the crash!
                raise HTTPException(status_code=404, detail="Patient not found in database")
                
            return {"status": "GRANTED_VIA_OVERRIDE", "patient": dict(patient), "audit": audit_entry}

        if not is_authorized:
            audit_entry = await log_access_event(current_user_id, "ACCESS_DENIED", req.patient_id, "Shift inactive or ward mismatch")
            raise HTTPException(status_code=403, detail={"message": "Access Denied", "audit": audit_entry})

        audit_entry = await log_access_event(current_user_id, "RECORD_ACCESSED", req.patient_id)
        patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", req.patient_id)
        
        if not patient: # <--- NEW CHECK HERE: Stops the crash!
            raise HTTPException(status_code=404, detail="Patient not found in database")
            
        return {"status": "GRANTED", "patient": dict(patient), "audit": audit_entry}

# --- 4. THE AUDIT LOG ENDPOINT (FOR THE CPO DASHBOARD) ---
@app.get("/api/audit-logs")
async def get_audit_logs():
    # Notice we are using db.audit_pool to match your audit_service!
    async with db.audit_pool.acquire() as conn:
        logs = await conn.fetch(
            "SELECT timestamp, user_id, target_patient_id, action, current_hash FROM audit_log ORDER BY timestamp DESC LIMIT 15"
        )
        
        return [
            {
                "timestamp": str(log["timestamp"]),
                "provider_id": log["user_id"],              # Mapping to frontend
                "patient_id": log["target_patient_id"],     # Mapping to frontend
                "action": log["action"],
                "current_hash": log["current_hash"]
            } for log in logs
        ]