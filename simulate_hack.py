import asyncio
import asyncpg

async def hack_database():
    print("💀 Connecting to Audit Database as rogue insider...")
    
    # Using your exact credentials and database name
    # Note: I assumed your username is 'postgres'. If it is different, change 'postgres' below!
    db_url = "postgresql://postgres:2993@localhost:5432/wardvault_audit_db"
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Find a log entry where a user was blocked/denied
        log = await conn.fetchrow("SELECT entry_id FROM audit_log WHERE action LIKE '%DENIED%' LIMIT 1")
        
        if log:
            entry_id = log['entry_id']
            print(f"😈 Target acquired: Log Entry #{entry_id} (Blocked Access)")
            print("💉 Injecting false data: Changing 'DENIED' to 'ACCESS_GRANTED_BY_ADMIN'...")
            
            # The Attack: We change the action text, but WE DO NOT update the SHA-256 hash
            await conn.execute("UPDATE audit_log SET action = 'ACCESS_GRANTED_BY_ADMIN' WHERE entry_id = $1", entry_id)
            
            print("✅ Hack successful. The record was altered silently at the database level.")
        else:
            print("⚠️ No blocked attempts found to hack.")
            print("💡 FIX: Go to your login page, log in as a Clerk or non-doctor, and try to access a record to generate a 'DENIED' log. Then run this script again!")
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(hack_database())