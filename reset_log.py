import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def wipe_slate_clean():
    conn = await asyncpg.connect(os.getenv("AUDIT_DB_URL"))
    # This deletes old logs and resets the entry_id counter back to 1
    await conn.execute("TRUNCATE audit_log RESTART IDENTITY;")
    await conn.close()
    print("✨ Audit log wiped clean! Ready for the live demo.")

if __name__ == "__main__":
    asyncio.run(wipe_slate_clean())