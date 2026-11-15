-- WardVault Audit Ledger Export (PostgreSQL compatible)

DROP TABLE IF EXISTS audit_log CASCADE;

CREATE TABLE audit_log (entry_id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id VARCHAR(100), action VARCHAR(100), target_patient_id VARCHAR(100), reason TEXT, previous_hash VARCHAR(64), current_hash VARCHAR(64));

INSERT INTO audit_log (timestamp, user_id, action, target_patient_id, reason, previous_hash, current_hash) VALUES ('2026-09-03 11:34:45', 'SYSTEM', 'SYSTEM_INIT', 'ALL', 'Initial genesis block', '0000000000000000000000000000000000000000000000000000000000000000', 'f763eea0d31855caf42ff6e8b83c76d69c3125632100361e318f142c64b9ffaa');
