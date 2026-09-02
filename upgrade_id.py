import asyncio
import asyncpg
import random

LEGACY_DB_URL = "postgresql://postgres:2993@localhost:5432/hospital_legacy_db"
AUDIT_DB_URL = "postgresql://postgres:2993@localhost:5432/wardvault_audit_db"

async def master_migrate():
    print("🚀 Initializing Crash-Proof Master ID Migration & Rebranding...")
    
    legacy_conn = await asyncpg.connect(LEGACY_DB_URL)
    audit_conn = await asyncpg.connect(AUDIT_DB_URL)
    
    try:
        # 1. Temporarily pause foreign key triggers
        await legacy_conn.execute("ALTER TABLE providers DISABLE TRIGGER ALL;")
        try:
            await legacy_conn.execute("ALTER TABLE active_shifts DISABLE TRIGGER ALL;")
        except:
            pass 
        
        # 2. Fetch all providers alongside their organizations
        providers = await legacy_conn.fetch("SELECT id, speciality, organization FROM providers")
        
        dept_map = {
            "Surgery": "SUR",
            "IT Admin": "ITA",
            "Neurology": "NEU",
            "Emergency Medicine": "EME",
            "Cardiology": "CAR",
            "Pediatrics": "PED",
            "Billing Clerk": "BIL"
        }
        
        uch_count = 0
        jaja_count = 0
        used_ids = set() # Track generated IDs to prevent duplicates

        for p in providers:
            old_id = p["id"]
            dept = dept_map.get(p["speciality"], "GEN")
            org = p["organization"] or "ORG-UCH"
            
            prefix = "JAJA" if "JAJA" in org else "UCH"
            if prefix == "JAJA":
                jaja_count += 1
            else:
                uch_count += 1
                
            # Generate a unique serial number that doesn't collide
            counter = random.randint(2000, 9999)
            new_id = f"{prefix}/26/{dept}/{counter}"
            
            while new_id in used_ids:
                counter = random.randint(2000, 9999)
                new_id = f"{prefix}/26/{dept}/{counter}"
                
            used_ids.add(new_id)
            
            # 3. Update Legacy Database
            await legacy_conn.execute("UPDATE providers SET id = $1 WHERE id = $2", new_id, old_id)
            try:
                await legacy_conn.execute("UPDATE active_shifts SET provider_id = $1 WHERE provider_id = $2", new_id, old_id)
            except:
                pass
            
            # 4. Update Audit Database
            await audit_conn.execute("UPDATE audit_log SET user_id = $1 WHERE user_id = $2", new_id, old_id)

        # 5. Restore triggers
        await legacy_conn.execute("ALTER TABLE providers ENABLE TRIGGER ALL;")
        try:
            await legacy_conn.execute("ALTER TABLE active_shifts ENABLE TRIGGER ALL;")
        except:
            pass
        
        print(f"✅ Migration Complete without collisions!")
        print(f"🏥 Updated {uch_count} UCH staff to 'UCH/26/DEPT/...' format.")
        print(f"🩺 Updated {jaja_count} JAJA staff to 'JAJA/26/DEPT/...' format.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await legacy_conn.close()
        await audit_conn.close()

if __name__ == "__main__":
    asyncio.run(master_migrate())