import os
import re
import aiosqlite
from contextlib import asynccontextmanager

USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() in ("true", "1", "yes")
LEGACY_DB_URL = os.getenv("LEGACY_DB_URL", "postgresql://postgres:2993@localhost:5432/hospital_legacy_db")
AUDIT_DB_URL = os.getenv("AUDIT_DB_URL", "postgresql://postgres:2993@localhost:5432/wardvault_audit_db")

CLINICAL_SQLITE_PATH = os.path.abspath("wardvault_clinical.db")
AUDIT_SQLITE_PATH = os.path.abspath("wardvault_audit.db")

class SqliteRecord(dict):
    """Dict subclass that allows dictionary access, .get(), and numeric index access."""
    def __init__(self, cols, row):
        super().__init__()
        for c, v in zip(cols, row):
            self[c] = v
        self._values = row

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

class SqliteConnectionWrapper:
    """Wraps an aiosqlite connection to provide an asyncpg-compatible API."""
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    def _prepare_sql(self, sql: str) -> str:
        # Translate PostgreSQL $1, $2, ... to SQLite ?
        translated = re.sub(r"\$\d+", "?", sql)
        # Translate ILIKE to LIKE (SQLite LIKE is case-insensitive for ASCII)
        translated = re.sub(r"\bILIKE\b", "LIKE", translated, flags=re.IGNORECASE)
        # Handle TRUNCATE TABLE ... RESTART IDENTITY
        if "TRUNCATE" in translated.upper() and "AUDIT_LOG" in translated.upper():
            return "DELETE FROM audit_log"
        return translated

    async def fetchrow(self, query: str, *args):
        prepared = self._prepare_sql(query)
        async with self._conn.execute(prepared, args) as cursor:
            row = await cursor.fetchone()
            if prepared.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
                await self._conn.commit()
            if row is None:
                return None
            cols = [c[0] for c in cursor.description]
            return SqliteRecord(cols, row)

    async def fetch(self, query: str, *args):
        prepared = self._prepare_sql(query)
        async with self._conn.execute(prepared, args) as cursor:
            rows = await cursor.fetchall()
            if prepared.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
                await self._conn.commit()
            cols = [c[0] for c in cursor.description]
            return [SqliteRecord(cols, r) for r in rows]

    async def fetchval(self, query: str, *args):
        prepared = self._prepare_sql(query)
        async with self._conn.execute(prepared, args) as cursor:
            row = await cursor.fetchone()
            if prepared.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
                await self._conn.commit()
            if row is None:
                return None
            return row[0]

    async def execute(self, query: str, *args):
        prepared = self._prepare_sql(query)
        res = await self._conn.execute(prepared, args)
        await self._conn.commit()
        return res

    @asynccontextmanager
    async def transaction(self):
        # Transaction context manager
        try:
            yield self
            await self._conn.commit()
        except Exception:
            await self._conn.rollback()
            raise

class SqlitePoolWrapper:
    """Emulates asyncpg connection pool using aiosqlite."""
    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def acquire(self):
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            wrapper = SqliteConnectionWrapper(conn)
            yield wrapper

    async def close(self):
        pass

class Database:
    def __init__(self):
        self.legacy_pool = None
        self.audit_pool = None
        self.is_sqlite = False

    async def connect(self):
        if USE_POSTGRES:
            try:
                import asyncpg
                print(f"Connecting to PostgreSQL: {LEGACY_DB_URL}")
                self.legacy_pool = await asyncpg.create_pool(dsn=LEGACY_DB_URL, min_size=2, max_size=10)
                self.audit_pool = await asyncpg.create_pool(dsn=AUDIT_DB_URL, min_size=2, max_size=10)
                print("✅ Connected to PostgreSQL databases.")
                return
            except Exception as e:
                print(f"⚠️ PostgreSQL connection failed: {e}. Falling back to SQLite.")

        # Default to SQLite
        self.is_sqlite = True
        self.legacy_pool = SqlitePoolWrapper(CLINICAL_SQLITE_PATH)
        self.audit_pool = SqlitePoolWrapper(AUDIT_SQLITE_PATH)
        print(f"✅ WardVault running on SQLite:")
        print(f"   Clinical DB: {CLINICAL_SQLITE_PATH}")
        print(f"   Audit DB:    {AUDIT_SQLITE_PATH}")

    async def disconnect(self):
        if self.legacy_pool:
            await self.legacy_pool.close()
        if self.audit_pool:
            await self.audit_pool.close()
        print("Database connections closed.")

db = Database()
