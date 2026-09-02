import asyncio
import asyncpg
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_audit_chain():
    print("Initiating WardVault Cryptographic Integrity Check...\n")
    
    # Connect to your audit database
    conn = await asyncpg.connect(os.getenv("AUDIT_DB_URL"))
    
    # Fetch all logs in order
    records = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")
    
    if not records:
        print("Audit log is empty.")
        return

    is_valid = True
    expected_previous = "0" * 64
    
    for row in records:
        entry_id = row['entry_id']
        user_id = row['user_id']
        action = row['action']
        patient_id = row['target_patient_id'] or ""
        reason = row['reason'] or ""
        prev_hash = row['previous_hash']
        curr_hash = row['current_hash']
        
        # 1. Check the link to the previous record
        if prev_hash != expected_previous:
            print(f"❌ CHAIN BROKEN at Entry {entry_id}: Previous hash does not match!")
            is_valid = False
            break
            
        # 2. Recompute the math to ensure data wasn't altered
        payload = f"{user_id}|{action}|{patient_id}|{reason}|{prev_hash}"
        recomputed_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        
        if recomputed_hash != curr_hash:
            print(f"❌ TAMPERING DETECTED at Entry {entry_id}: Data was secretly altered!")
            is_valid = False
            break
            
        print(f"✅ Entry {entry_id}: Integrity Verified (Hash: {curr_hash[:8]}...)")
        expected_previous = curr_hash

    await conn.close()
    
    print("\n-------------------------------------------------")
    if is_valid:
        print("🛡️  SYSTEM SECURE: 0 Tampering Incidents Detected.")
    else:
        print("🚨 SYSTEM COMPROMISED: Audit log integrity failure.")
    print("-------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(verify_audit_chain())