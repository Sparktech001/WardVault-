import asyncpg

# Hardcode the URLs temporarily to bypass the Windows .env issue
LEGACY_DB_URL = "postgresql://postgres:2993@localhost:5432/hospital_legacy_db"
AUDIT_DB_URL = "postgresql://postgres:2993@localhost:5432/wardvault_audit_db"

print(f"DEBUG - Forcing Legacy URL: {LEGACY_DB_URL}")

class Database:
    def __init__(self):
        self.legacy_pool = None
        self.audit_pool = None

    async def connect(self):
        self.legacy_pool = await asyncpg.create_pool(dsn=LEGACY_DB_URL, min_size=2, max_size=10)
        self.audit_pool = await asyncpg.create_pool(dsn=AUDIT_DB_URL, min_size=2, max_size=10)
        print("Connected to hospital_legacy_db and wardvault_audit_db.")

    async def disconnect(self):
        if self.legacy_pool:
            await self.legacy_pool.close()
        if self.audit_pool:
            await self.audit_pool.close()
        print("Database pools closed.")

# THIS IS THE LINE YOU WERE MISSING
db = Database()