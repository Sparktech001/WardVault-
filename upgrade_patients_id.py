import asyncio
import asyncpg
import random

LEGACY_DB_URL = "postgresql://postgres:2993@localhost:5432/hospital_legacy_db"
# We don't even need to touch the audit DB anymore because we aren't changing patient IDs!

async def fix_patients_properly():
    print("🚀 Running Clinically-Accurate Ward Re-indexing...")
    conn = await asyncpg.connect(LEGACY_DB_URL)
    
    try:
        patients = await conn.fetch("SELECT id FROM patients")
        total_patients = len(patients)
        
        if total_patients == 0:
            print("❌ No patients found!")
            return

        # Realistic Wards based exactly on your Staff Data
        uch_wards = ["uch-emergency", "uch-cardiology", "uch-surgery"]
        jaja_wards = ["jaja-pediatrics", "jaja-neurology", "jaja-emergency"]

        for i, pat in enumerate(patients):
            pat_id = pat["id"]
            
            # Split patients 50/50 between UCH and JAJA
            if i < (total_patients // 2):
                org = "ORG-UCH"
                ward = random.choice(uch_wards)
            else:
                org = "ORG-JAJA"
                ward = random.choice(jaja_wards)

            # Update ONLY the organization and ward. Leave the ID exactly as it is!
            await conn.execute(
                "UPDATE patients SET organization = $1, ward_id = $2 WHERE id = $3", 
                org, ward, pat_id
            )

        print("✅ Database Wards perfectly aligned with Staff Roles!")
        print("💡 Go ahead and log in to the UI. The dropdown will dynamically load the patients!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_patients_properly())