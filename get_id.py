import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def show_users():
    # Connects to your hospital database
    conn = await asyncpg.connect(os.getenv("LEGACY_DB_URL"))
    users = await conn.fetch("SELECT id, speciality FROM providers")
    
    print("\n=== AVAILABLE TEST USERS ===")
    for u in users:
        print(f"Username ID: {u['id']}  -->  Role: {u['speciality']}")
    print("===========================\n")
    print("Password for all is: password123")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(show_users())