import zipfile
import csv
import io
import re
import os
import sqlite3
import random
import hashlib
from datetime import datetime, timedelta
from passlib.context import CryptContext

ZIP_PATH = r"C:\Users\LENOVO PC\Downloads\synthea_sample_data_csv_latest.zip"
CLINICAL_DB_PATH = "wardvault_clinical.db"
AUDIT_DB_PATH = "wardvault_audit.db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD_HASH = pwd_context.hash("password123")

def clean_name(val):
    if not val:
        return ""
    return re.sub(r"\d+", "", val).strip()

def calculate_age(birthdate_str):
    try:
        b_date = datetime.strptime(birthdate_str, "%Y-%m-%d")
        today = datetime.now()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except Exception:
        return random.randint(18, 65)

def restore_phc_database():
    print("🏥 Restoring WardVault for Primary Healthcare Centre (PHC) Operations...")

    # Key PHC Demo Staff
    phc_staff = [
        ("PHC/26/INC/104", "Alakia Primary Health Centre", "Dr. Raphael Thompson", "Facility In-Charge", DEFAULT_PASSWORD_HASH, True),
        ("PHC/26/NUR/103", "Alakia Primary Health Centre", "Folake Adeleke", "Nurse / Midwife", DEFAULT_PASSWORD_HASH, True),
        ("PHC/26/CHEW/102", "Alakia Primary Health Centre", "Amina Bello", "CHEW", DEFAULT_PASSWORD_HASH, True),
        ("PHC/26/REC/101", "Alakia Primary Health Centre", "Ibrahim Musa", "Records Officer", DEFAULT_PASSWORD_HASH, True),
        ("PHC/26/CHEW/105", "Alakia Primary Health Centre", "Vernita Cartwright", "CHEW", DEFAULT_PASSWORD_HASH, False), # Off duty
        ("PHC/26/NUR/106", "Alakia Primary Health Centre", "Concha Mann", "Nurse / Midwife", DEFAULT_PASSWORD_HASH, False), # Off duty
    ]

    # Additional staff to preserve all 278 Synthea providers mapped to PHC departments
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH) as z:
            with z.open("synthea_sample_data_csv_latest/providers.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                for i, r in enumerate(reader):
                    if i < 6:
                        continue
                    p_name = clean_name(r["NAME"])
                    role = random.choice(["CHEW", "Nurse / Midwife", "Records Officer", "Community Health Worker"])
                    role_code = "CHEW" if "CHEW" in role else "NUR" if "Nurse" in role else "REC"
                    p_id = f"PHC/26/{role_code}/{2000 + i}"
                    phc_staff.append((
                        p_id,
                        "Alakia Primary Health Centre",
                        p_name,
                        role,
                        DEFAULT_PASSWORD_HASH,
                        True
                    ))

    # Read Conditions from Synthea
    conditions_by_patient = {}
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH) as z:
            with z.open("synthea_sample_data_csv_latest/conditions.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                for r in reader:
                    pat_id = r["PATIENT"]
                    desc = r["DESCRIPTION"]
                    if "education" not in desc.lower() and "employment" not in desc.lower():
                        conditions_by_patient[pat_id] = desc

    # Patients list
    patients = []
    # Core Demo Patients for PHC scenarios
    demo_patients = [
        ("PHC-PT-001", "Zainab", "Aliyu", "Zainab Aliyu", 26, "F", "Alakia PHC", "ANC-042", "Uncomplicated Malaria (Pregnancy 2nd Trimester)", "O+", "AA", "08031234567", "NIN-8930214819", "BHCPF-OY-4921", "Penicillin"),
        ("PHC-PT-002", "Babatunde", "Ogunleye", "Babatunde Ogunleye", 54, "M", "Alakia PHC", "MED-118", "Essential Hypertension & Type 2 Diabetes", "A+", "AS", "08029876543", "NIN-2910394821", "BHCPF-OY-1092", "None"),
        ("PHC-PT-003", "Chinedu", "Eze", "Chinedu Eze", 4, "M", "Alakia PHC", "IMM-089", "Severe Acute Malnutrition & Fever", "B+", "AA", "08145556677", "NIN-4491029384", "BHCPF-OY-8832", "Sulfa drugs"),
        ("PHC-PT-004", "Maryam", "Sani", "Maryam Sani", 19, "F", "Alakia PHC", "ANC-091", "Antenatal Routine Checkup (Week 28)", "O+", "AC", "07011223344", "NIN-9102938475", "BHCPF-OY-5712", "None"),
        ("PHC-PT-005", "Emeka", "Okafor", "Emeka Okafor", 38, "M", "Alakia PHC", "SUR-014", "Suspected Acute Appendicitis (Needs Secondary Referral)", "O-", "AA", "08099887766", "NIN-1928374650", "BHCPF-OY-3319", "None")
    ]

    for dp in demo_patients:
        patients.append(dp)

    # Read remaining from Synthea
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH) as z:
            with z.open("synthea_sample_data_csv_latest/patients.csv") as f:
                reader = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")))
                for i, r in enumerate(reader):
                    pat_raw_id = r["Id"]
                    first = clean_name(r.get("FIRST", ""))
                    last = clean_name(r.get("LAST", ""))
                    full_name = f"{first} {last}".strip()
                    gender = r.get("GENDER", "M")
                    age = calculate_age(r.get("BIRTHDATE", "1990-01-01"))
                    folder_no = f"FL-{1000 + i}"
                    condition = conditions_by_patient.get(pat_raw_id, "Acute Upper Respiratory Infection")
                    short_id = f"PHC-PT-{100 + i}"
                    nin = f"NIN-{random.randint(1000000000, 9999999999)}"
                    bhcpf = f"BHCPF-OY-{random.randint(1000, 9999)}"
                    blood_group = random.choice(["O+", "A+", "B+", "AB+", "O-"])
                    genotype = random.choice(["AA", "AA", "AA", "AS", "AC"])

                    patients.append((
                        short_id, first, last, full_name, age, gender,
                        "Alakia PHC", folder_no, condition, blood_group,
                        genotype, "080" + str(random.randint(10000000, 99999999)),
                        nin, bhcpf, "None reported"
                    ))

    # Recreate Clinical Database
    if os.path.exists(CLINICAL_DB_PATH):
        os.remove(CLINICAL_DB_PATH)

    conn_clin = sqlite3.connect(CLINICAL_DB_PATH)
    cur_clin = conn_clin.cursor()

    # Providers
    cur_clin.execute("""
        CREATE TABLE providers (
            id VARCHAR PRIMARY KEY,
            organization VARCHAR,
            name VARCHAR,
            speciality VARCHAR,
            password_hash VARCHAR,
            is_on_duty BOOLEAN DEFAULT 1
        )
    """)

    # Patients (Adapted for PHC)
    cur_clin.execute("""
        CREATE TABLE patients (
            id VARCHAR PRIMARY KEY,
            first VARCHAR,
            last VARCHAR,
            name VARCHAR,
            age INTEGER,
            gender VARCHAR,
            organization VARCHAR,
            ward_id VARCHAR,
            condition VARCHAR,
            blood_group VARCHAR,
            genotype VARCHAR,
            phone VARCHAR,
            nin VARCHAR,
            bhcpf_id VARCHAR,
            allergies VARCHAR
        )
    """)

    # Outpatient Clinical Encounters
    cur_clin.execute("""
        CREATE TABLE clinical_encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            provider_id VARCHAR,
            encounter_type VARCHAR,
            bp VARCHAR,
            temperature REAL,
            pulse INTEGER,
            weight REAL,
            rdt_result VARCHAR,
            clinical_assessment TEXT,
            prescription TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (provider_id) REFERENCES providers(id)
        )
    """)

    # Clinical Notes (Append-only & Corrections)
    cur_clin.execute("""
        CREATE TABLE clinical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            provider_id VARCHAR,
            note_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            correction_reason VARCHAR,
            supersedes_note_id INTEGER
        )
    """)

    # Referrals (PHC to Secondary Hospital)
    cur_clin.execute("""
        CREATE TABLE referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            referred_by VARCHAR,
            destination_facility VARCHAR,
            reason TEXT,
            urgency VARCHAR,
            status VARCHAR DEFAULT 'Referred',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (referred_by) REFERENCES providers(id)
        )
    """)

    # Paper Records Migration Tracking
    cur_clin.execute("""
        CREATE TABLE paper_intakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            folder_number VARCHAR,
            transcribed_by VARCHAR,
            flagged_for_review BOOLEAN DEFAULT 0,
            review_notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Populate providers
    cur_clin.executemany(
        "INSERT INTO providers (id, organization, name, speciality, password_hash, is_on_duty) VALUES (?, ?, ?, ?, ?, ?)",
        phc_staff
    )

    # Populate patients
    cur_clin.executemany(
        """INSERT INTO patients (
            id, first, last, name, age, gender, organization, ward_id, condition,
            blood_group, genotype, phone, nin, bhcpf_id, allergies
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        patients
    )

    # Sample Initial Clinical Encounter
    cur_clin.execute("""
        INSERT INTO clinical_encounters (
            patient_id, provider_id, encounter_type, bp, temperature, pulse, weight,
            rdt_result, clinical_assessment, prescription, timestamp
        ) VALUES (
            'PHC-PT-001', 'PHC/26/CHEW/102', 'Antenatal / Malaria Screening',
            '118/76', 38.2, 88, 62.5, 'Positive (P. falciparum)',
            'Patient in 2nd trimester presenting with fever, chills, and mild headache. RDT positive for malaria.',
            'Artemether-Lumefantrine (Coartem) dispersible, Paracetamol 500mg, Oral Rehydration Salts',
            '2026-09-03 09:15:00'
        )
    """)

    # Sample Initial Note
    cur_clin.execute("""
        INSERT INTO clinical_notes (patient_id, provider_id, note_text, timestamp)
        VALUES ('PHC-PT-001', 'PHC/26/CHEW/102', 'Patient counseled on insecticide-treated net (ITN) usage and adequate hydration.', '2026-09-03 09:25:00')
    """)

    # Sample Initial Referral
    cur_clin.execute("""
        INSERT INTO referrals (
            patient_id, referred_by, destination_facility, reason, urgency, status, created_at
        ) VALUES (
            'PHC-PT-005', 'PHC/26/INC/104', 'State Specialist Hospital / UCH',
            'Severe rebound abdominal tenderness in RLQ with high fever. Suspected acute appendicitis requiring emergency surgical evaluation.',
            'Urgent', 'Referred', '2026-09-03 10:45:00'
        )
    """)

    # Sample Paper Intake Record
    cur_clin.execute("""
        INSERT INTO paper_intakes (patient_id, folder_number, transcribed_by, flagged_for_review, review_notes)
        VALUES ('PHC-PT-002', 'MED-118', 'PHC/26/REC/101', 0, 'Clean transcription of 2025 hypertensive clinic paper chart.')
    """)
    cur_clin.execute("""
        INSERT INTO paper_intakes (patient_id, folder_number, transcribed_by, flagged_for_review, review_notes)
        VALUES ('PHC-PT-003', 'IMM-089', 'PHC/26/REC/101', 1, 'Smudged handwriting on dose schedule for measles vaccine. Flagged for Nurse Folake review.')
    """)

    conn_clin.commit()
    conn_clin.close()

    # Recreate Audit Database
    if os.path.exists(AUDIT_DB_PATH):
        os.remove(AUDIT_DB_PATH)

    conn_audit = sqlite3.connect(AUDIT_DB_PATH)
    cur_audit = conn_audit.cursor()

    cur_audit.execute("""
        CREATE TABLE audit_log (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR,
            action VARCHAR,
            target_patient_id VARCHAR,
            reason VARCHAR,
            previous_hash VARCHAR,
            current_hash VARCHAR
        )
    """)

    prev_hash = "0" * 64
    reason = "WardVault PHC Gateway Genesis Block"
    payload = f"SYSTEM|SYSTEM_INIT|ALL|{reason}|{prev_hash}"
    gen_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    cur_audit.execute("""
        INSERT INTO audit_log (timestamp, user_id, action, target_patient_id, reason, previous_hash, current_hash)
        VALUES ('2026-09-03 08:00:00', 'SYSTEM', 'SYSTEM_INIT', 'ALL', ?, ?, ?)
    """, (reason, prev_hash, gen_hash))

    conn_audit.commit()
    conn_audit.close()

    print(f"✅ WardVault PHC Database Seeding Complete!")
    print(f"   - Providers: {len(phc_staff)}")
    print(f"   - Patients: {len(patients)}")
    print(f"   - Encounters, Referrals, and Paper Migration queues initialized.")

if __name__ == "__main__":
    restore_phc_database()
