import asyncio
import asyncpg
from datetime import timezone, timedelta

# Hardcoded URL to bypass the Windows .env issue
AUDIT_DB_URL = "postgresql://postgres:2993@localhost:5432/wardvault_audit_db"

# Create a timezone object for West Africa Time (UTC+1)
WAT = timezone(timedelta(hours=1))

async def show_logs():
    conn = await asyncpg.connect(AUDIT_DB_URL)
    
    # Fetch all records from the audit_log table
    records = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")
    
    print("\n--- 🛡️ WARDVAULT AUDIT VAULT 🛡️ ---")
    if not records:
        print("The vault is currently empty.")
        
    for row in records:
        # Convert the UTC database time to your local time (UTC+1)
        local_time = row['timestamp'].astimezone(WAT)
        
        # Format it nicely so it drops the long milliseconds
        formatted_time = local_time.strftime('%Y-%m-%d %I:%M:%S %p')
        
        print(f"[{formatted_time}] Entry {row['entry_id']} | Action: {row['action']} | Target Patient: {row['target_patient_id']}")
        print(f"Reason: {row['reason']}")
        print(f"Hash: {row['current_hash'][:15]}...\n")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(show_logs())