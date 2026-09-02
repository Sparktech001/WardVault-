import asyncio
import asyncpg

LEGACY_DB_URL = "postgresql://postgres:2993@localhost:5432/hospital_legacy_db"

async def partition_facilities():
    conn = await asyncpg.connect(LEGACY_DB_URL)
    
    try:
        print("🚀 Partitioning database into UCH and JAJA...")
        
        # Ensure necessary columns exist safely
        await conn.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS organization VARCHAR(100);")
        await conn.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS organization VARCHAR(100);")
        await conn.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS ward_id VARCHAR(100);")
        
        # 1. Assign the first 140 providers and patients to UCH
        await conn.execute("""
            UPDATE providers SET organization = 'ORG-UCH' 
            WHERE id IN (SELECT id FROM providers ORDER BY id LIMIT 140)
        """)
        await conn.execute("""
            UPDATE patients SET organization = 'ORG-UCH', ward_id = 'uch-icu' 
            WHERE id IN (SELECT id FROM patients ORDER BY id LIMIT 140)
        """)

        # 2. Assign the rest to JAJA Clinic
        await conn.execute("""
            UPDATE providers SET organization = 'ORG-JAJA' 
            WHERE organization IS NULL OR organization != 'ORG-UCH'
        """)
        await conn.execute("""
            UPDATE patients SET organization = 'ORG-JAJA', ward_id = 'NONE' 
            WHERE organization IS NULL OR organization != 'ORG-UCH'
        """)

        print("✅ Database successfully partitioned into UCH and JAJA!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(partition_facilities())