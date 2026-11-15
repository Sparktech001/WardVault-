import asyncio
from datetime import timezone, timedelta
from database import db

# Create a timezone object for West Africa Time (UTC+1)
WAT = timezone(timedelta(hours=1))

async def show_logs():
    await db.connect()
    try:
        async with db.audit_pool.acquire() as conn:
            records = await conn.fetch("SELECT * FROM audit_log ORDER BY entry_id ASC")
            
            print("\n--- 🛡️ WARDVAULT AUDIT VAULT 🛡️ ---")
            if not records:
                print("The vault is currently empty.")
                
            for row in records:
                ts = row['timestamp']
                # Support string or datetime timestamps
                print(f"[{ts}] Entry {row['entry_id']} | Action: {row['action']} | Target Patient: {row['target_patient_id']}")
                print(f"Reason: {row['reason']}")
                print(f"Hash: {row['current_hash'][:15]}...\n")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(show_logs())
