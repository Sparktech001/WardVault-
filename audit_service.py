import hashlib
from database import db

async def log_access_event(user_id: str, action: str, target_patient_id: str = None, reason: str = None):
    async with db.audit_pool.acquire() as conn:
        async with conn.transaction():
            last_entry = await conn.fetchrow(
                "SELECT current_hash FROM audit_log ORDER BY entry_id DESC LIMIT 1"
            )
            
            previous_hash = last_entry["current_hash"] if last_entry else ("0" * 64)
            payload = f"{user_id}|{action}|{target_patient_id or ''}|{reason or ''}|{previous_hash}"
            current_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            row = await conn.fetchrow(
                """
                INSERT INTO audit_log (user_id, action, target_patient_id, reason, previous_hash, current_hash)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING entry_id, current_hash, timestamp
                """,
                user_id, action, target_patient_id, reason, previous_hash, current_hash
            )
            
            return {
                "entry_id": row["entry_id"],
                "previous_hash": previous_hash,
                "current_hash": row["current_hash"],
                "timestamp": str(row["timestamp"]) # <--- Fixed here!
            }