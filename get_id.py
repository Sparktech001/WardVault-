import asyncio
from database import db

async def show_users():
    await db.connect()
    try:
        async with db.legacy_pool.acquire() as conn:
            users = await conn.fetch("SELECT id, name, speciality, organization FROM providers ORDER BY id ASC")
            
            print("\n=== AVAILABLE TEST USERS ===")
            # Highlight known demo users first
            demo_ids = [
                "UCH/26/EME/2980",
                "UCH/26/BIL/6703",
                "UCH/26/EME/6767",
                "UCH/26/CAR/4364",
                "JAJA/26/EME/4388",
                "JAJA/26/PED/5700"
            ]
            print("\n--- Key Demo Accounts ---")
            for u in users:
                if u['id'] in demo_ids:
                    print(f"Username ID: {u['id']:<18} Name: {u.get('name',''):<22} Role: {u['speciality']:<20} Org: {u['organization']}")
            
            print("\n--- Other Available Staff (Sample) ---")
            sample_count = 0
            for u in users:
                if u['id'] not in demo_ids and sample_count < 10:
                    print(f"Username ID: {u['id']:<18} Name: {u.get('name',''):<22} Role: {u['speciality']:<20} Org: {u['organization']}")
                    sample_count += 1
            print(f"... and {len(users) - len(demo_ids) - sample_count} more providers.")
            print("===========================\n")
            print("Default password for all users is: password123\n")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(show_users())
