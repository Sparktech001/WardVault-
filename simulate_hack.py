import asyncio
from database import db

async def hack_database():
    print("💀 Connecting to Audit Database as rogue insider...")
    
    await db.connect()
    try:
        async with db.audit_pool.acquire() as conn:
            # Find a log entry where a user was blocked/denied or any non-genesis entry
            log = await conn.fetchrow("SELECT entry_id FROM audit_log WHERE action LIKE '%DENIED%' OR entry_id > 1 LIMIT 1")
            
            if log:
                entry_id = log['entry_id']
                print(f"😈 Target acquired: Log Entry #{entry_id}")
                print("💉 Injecting false data: Changing action text without updating SHA-256 hash...")
                
                # The Attack: We change the action text, but WE DO NOT update the SHA-256 hash
                await conn.execute("UPDATE audit_log SET action = 'ACCESS_GRANTED_BY_ADMIN' WHERE entry_id = $1", entry_id)
                
                print("✅ Hack successful. The record was altered silently at the database level.")
            else:
                print("⚠️ No log entries found to hack. Access records through the gateway to generate logs first.")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(hack_database())
