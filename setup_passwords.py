import asyncio
import asyncpg
import os
from auth import get_password_hash
from dotenv import load_dotenv

load_dotenv()

async def apply_passwords():
    print("Connecting to database...")
    conn = await asyncpg.connect(os.getenv("LEGACY_DB_URL")) 
    
    print("Adding password_hash column...")
    await conn.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);")

    print("Setting default passwords...")
    default_hash = get_password_hash("password123")
    await conn.execute(
        "UPDATE providers SET password_hash = $1 WHERE password_hash IS NULL", 
        default_hash
    )
    
    await conn.close()
    print("✅ Success! All test users now have 'password123' as their password.")

if __name__ == "__main__":
    asyncio.run(apply_passwords())