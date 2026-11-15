"""
WardVault PHC Database Seeding Script - OpenMRS-Aligned Local Architecture
Populates:
1. 10 Real-world Nigerian Primary Healthcare Personas with Hospital Numbers (HOSP-2026-001 to 010)
2. OpenMRS-style encounters with attending clinicians & test orders
3. Short-stay (1-3 days) and extended (up to 30-40 days) primary care admissions
4. Secondary referrals to UCH Ibadan with formal medical transfer letters
5. 4 Realistic PHC staff accounts
"""
import sqlite3
import hashlib
from datetime import datetime, timedelta
from auth import get_password_hash

CLINICAL_DB = "wardvault_clinical.db"
AUDIT_DB = "wardvault_audit.db"

# Bcrypt hash for 'password123'
DEFAULT_HASH = get_password_hash("password123")

def seed_database():
    conn = sqlite3.connect(CLINICAL_DB)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS clinical_encounters")
    cur.execute("DROP TABLE IF EXISTS clinical_notes")
    cur.execute("DROP TABLE IF EXISTS short_stay_admissions")
    cur.execute("DROP TABLE IF EXISTS referrals")
    cur.execute("DROP TABLE IF EXISTS paper_intakes")
    cur.execute("DROP TABLE IF EXISTS patients")
    cur.execute("DROP TABLE IF EXISTS providers")

    # 1. Staff Providers (4 Realistic PHC Roles)
    cur.execute("""
        CREATE TABLE providers (
            id VARCHAR PRIMARY KEY,
            organization VARCHAR,
            name VARCHAR,
            speciality VARCHAR,
            password_hash VARCHAR,
            is_on_duty BOOLEAN DEFAULT 1
        )
    """)

    providers = [
        ("PHC/26/NUR/103", "Alakia PHC", "Nurse Folake Adeyemi", "Staff Midwife / Nurse", DEFAULT_HASH, 1),
        ("PHC/26/CHEW/102", "Alakia PHC", "Amina Bello", "Community Health Extension Worker (CHEW)", DEFAULT_HASH, 1),
        ("PHC/26/REC/101", "Alakia PHC", "Ibrahim Musa", "Records Officer", DEFAULT_HASH, 1),
        ("PHC/26/MED/001", "Alakia PHC", "Dr. Kemi Sanni", "Facility In-Charge (Chief Medical Officer)", DEFAULT_HASH, 1),
        ("PHC/26/CHEW/105", "Alakia PHC", "Vernita Cartwright", "CHEW (Off Duty Demo)", DEFAULT_HASH, 0)
    ]
    cur.executemany("INSERT INTO providers VALUES (?, ?, ?, ?, ?, ?)", providers)

    # 2. Patients Table (Hospital Number as Primary Identifier)
    cur.execute("""
        CREATE TABLE patients (
            id VARCHAR PRIMARY KEY,
            hospital_number VARCHAR,
            first VARCHAR,
            last VARCHAR,
            name VARCHAR,
            age INTEGER,
            gender VARCHAR,
            organization VARCHAR,
            ward_id VARCHAR,
            clinic VARCHAR,
            condition VARCHAR,
            blood_group VARCHAR,
            genotype VARCHAR,
            phone VARCHAR,
            nin VARCHAR,
            bhcpf_id VARCHAR,
            allergies VARCHAR,
            is_new_digital BOOLEAN DEFAULT 0,
            has_paper_folder BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10 Curated Clinical Personas (Clean Primary Care Distribution: ANC, OPD, EPI)
    patients_data = [
        ("PHC-PT-001", "HOSP-2026-001", "Amina", "Garba", "Amina Garba", 26, "F", "Alakia PHC", "HOSP-2026-001", "ANC",
         "Pregnancy Care (32 Weeks Gestation)", "O+", "AA", "08031112233", "NIN-8920192831", "BHCPF-OY-4921", "Penicillin allergy", 0, 1),
        ("PHC-PT-002", "HOSP-2026-002", "Baby Kazeem", "Adeleke", "Baby Kazeem Adeleke", 0, "M", "Alakia PHC", "HOSP-2026-002", "EPI",
         "Newborn Routine 6-Week Immunization", "B+", "AA", "08023334455", "NIN-1928374650", "BHCPF-OY-1092", "None reported", 1, 0),
        ("PHC-PT-003", "HOSP-2026-003", "Joy", "Okafor", "Joy Okafor", 34, "F", "Alakia PHC", "HOSP-2026-003", "OPD",
         "HIV Routine Care (TLD Refill, Suppressed Viral Load)", "A+", "AS", "08145556677", "NIN-4491029384", "BHCPF-OY-8832", "Sulfa drugs", 0, 1),
        ("PHC-PT-004", "HOSP-2026-004", "Usman", "Danladi", "Usman Danladi", 42, "M", "Alakia PHC", "HOSP-2026-004", "OPD",
         "Tuberculosis (TB) Evaluation & 4-Drug Treatment", "O+", "AA", "07011223344", "NIN-9102938475", "BHCPF-OY-5712", "None reported", 0, 1),
        ("PHC-PT-005", "HOSP-2026-005", "Tunde", "Balogun", "Tunde Balogun", 19, "M", "Alakia PHC", "HOSP-2026-005", "OPD",
         "Severe Malaria (Admitted on IV Artesunate)", "O+", "AA", "08099887766", "NIN-1928374651", "BHCPF-OY-3319", "None reported", 0, 1),
        ("PHC-PT-006", "HOSP-2026-006", "Blessing", "Adeleke", "Blessing Adeleke", 29, "F", "Alakia PHC", "HOSP-2026-006", "OPD",
         "Postpartum Depression & Emotional Exhaustion", "B+", "AC", "08055443322", "NIN-6629104821", "BHCPF-OY-6621", "None reported", 0, 1),
        ("PHC-PT-007", "HOSP-2026-007", "Musa", "Ibrahim", "Musa Ibrahim", 35, "M", "Alakia PHC", "HOSP-2026-007", "OPD",
         "Okada Motorcycle Injury (Closed Tibia Fracture - Urgent Transfer to UCH)", "O-", "AA", "08129988776", "NIN-7718293041", "BHCPF-OY-7712", "None reported", 0, 1),
        ("PHC-PT-008", "HOSP-2026-008", "Chief Samuel", "Adele", "Chief Samuel Adele", 58, "M", "Alakia PHC", "HOSP-2026-008", "OPD",
         "Chronic High Blood Pressure & Type 2 Diabetes", "A+", "AS", "08077665544", "NIN-5519283746", "BHCPF-OY-2291", "None reported", 0, 1),
        ("PHC-PT-009", "HOSP-2026-009", "Baby Aisha", "Bello", "Baby Aisha Bello", 1, "F", "Alakia PHC", "HOSP-2026-009", "EPI",
         "Severe Acute Malnutrition (MUAC 11.2cm) - Inpatient Feeding Care", "O+", "AA", "08034567890", "NIN-3329104857", "BHCPF-OY-3318", "None reported", 1, 0),
        ("PHC-PT-010", "HOSP-2026-010", "Emmanuel", "Chukwu", "Emmanuel Chukwu", 7, "M", "Alakia PHC", "HOSP-2026-010", "OPD",
         "Routine School Child Health & Worm Treatment", "O+", "AA", "08091234567", "NIN-8829104756", "BHCPF-OY-9912", "None reported", 0, 1)
    ]

    cur.executemany("""
        INSERT INTO patients (
            id, hospital_number, first, last, name, age, gender, organization, ward_id,
            clinic, condition, blood_group, genotype, phone, nin, bhcpf_id,
            allergies, is_new_digital, has_paper_folder
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, patients_data)

    # 3. Clinical Encounters Table (OpenMRS Style: Attending Clinician + Structured Orders)
    cur.execute("""
        CREATE TABLE clinical_encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            provider_id VARCHAR,
            clinician_name VARCHAR,
            encounter_type VARCHAR,
            history_complaint TEXT,
            physical_exam TEXT,
            bp VARCHAR,
            temperature REAL,
            pulse INTEGER,
            weight REAL,
            blood_sugar REAL,
            investigations TEXT,
            primary_diagnosis VARCHAR,
            differential_diagnosis VARCHAR,
            prescription TEXT,
            outcome VARCHAR,
            followup_date VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed chronological encounters for returning patients
    encounters = [
        # Chief Samuel Adele (Patient 008) - 3 Chronological visits showing BP drop 160/98 -> 142/90 -> 126/82
        ("PHC-PT-008", "PHC/26/MED/001", "Dr. Kemi Sanni", "General Clinic",
         "Patient presented 3 months ago with persistent occipital headaches and dizziness for 2 weeks.",
         "Overweight middle-aged male. No ankle edema. Chest sounds clear.",
         "160/98", 37.0, 84, 78.2, 210.0,
         "Urinalysis: Trace protein, Fasting Blood Sugar: 210 mg/dL",
         "Uncontrolled Essential Hypertension (Stage 2) & Type 2 Diabetes",
         "Metabolic Syndrome",
         "Amlodipine 5mg daily + Metformin 500mg bd + Low-salt diet counseling",
         "Book Next Visit", (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
         (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")),

        ("PHC-PT-008", "PHC/26/MED/001", "Dr. Kemi Sanni", "General Clinic",
         "Patient returned for scheduled review. Headaches reduced. Compliant with diet.",
         "BP remains moderately elevated above target. No visual blurring.",
         "142/90", 36.7, 78, 76.5, 185.0,
         "Random Blood Sugar: 185 mg/dL",
         "Essential Hypertension (Stage 1) - Suboptimally Controlled",
         "Type 2 Diabetes",
         "Increased Amlodipine to 10mg daily + Metformin 500mg bd continued",
         "Book Next Visit", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
         (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")),

        ("PHC-PT-008", "PHC/26/NUR/103", "Nurse Folake Adeyemi", "General Clinic",
         "Routine monthly medication refill visit. No headache, no chest pain.",
         "Well-looking. Clear lung bases. Radial pulse regular.",
         "126/82", 36.8, 74, 75.5, 140.0,
         "Fasting Blood Sugar: 140 mg/dL (Glycemic control improved)",
         "Controlled Essential Hypertension & Controlled Type 2 Diabetes",
         "None",
         "Continue Amlodipine 10mg daily + Metformin 500mg bd (30-day refill dispensed)",
         "Give Drugs & Go Home", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
         (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),

        # Amina Garba (Patient 001) - Pregnancy ANC visit
        ("PHC-PT-001", "PHC/26/NUR/103", "Nurse Folake Adeyemi", "ANC & Maternity",
         "Routine 32-week ANC follow-up. Fetal movements active. Mild evening ankle puffiness.",
         "Fundal height 32cm, singleton longitudinal lie, cephalic presentation, FHR 142 bpm regular. Conjunctiva mild pallor.",
         "115/75", 36.6, 76, 68.0, 95.0,
         "PCV (Hemoglobin): 30%, Urinalysis: Negative for protein and glucose, Obstetric Ultrasound: Normal fetus",
         "Normal Third Trimester Pregnancy (32 Weeks Gestation) with Mild Anemia",
         "None",
         "Iron / Folic Acid daily + Fansidar (IPTp dose 2) stat + LLIN net reinforced",
         "Book Next Visit", (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
         (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")),

        # Joy Okafor (Patient 003) - HIV ART Refill
        ("PHC-PT-003", "PHC/26/CHEW/102", "Amina Bello", "General Clinic",
         "Routine 3-month ART refill visit. Patient is adherent, denies fever, cough, or diarrhea.",
         "General physical exam normal. No oral thrush, no lymphadenopathy.",
         "118/78", 36.5, 72, 61.0, 90.0,
         "Viral Load: <20 copies/mL (Undetectable). CD4 Count: 680 cells/uL.",
         "HIV-1 Infection (WHO Clinical Stage 1, Suppressed on ART)",
         "None",
         "Tenofovir/Lamivudine/Dolutegravir (TLD) 1 tablet daily (90-day refill dispensed)",
         "Book Next Visit", (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
         (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"))
    ]

    for enc in encounters:
        cur.execute("""
            INSERT INTO clinical_encounters (
                patient_id, provider_id, clinician_name, encounter_type, history_complaint, physical_exam,
                bp, temperature, pulse, weight, blood_sugar, investigations, primary_diagnosis,
                differential_diagnosis, prescription, outcome, followup_date, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, enc)

    # 4. Observation & Inpatient Admissions Table (Supports Short Stays & Extended 30-40 Days)
    cur.execute("""
        CREATE TABLE short_stay_admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            provider_id VARCHAR,
            clinician_name VARCHAR,
            bed_number VARCHAR,
            admission_type VARCHAR DEFAULT 'Short-Stay Observation',
            admission_reason VARCHAR,
            admitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            discharged_at TIMESTAMP,
            status VARCHAR DEFAULT 'Active',
            daily_ward_notes TEXT,
            discharge_summary TEXT
        )
    """)

    # Seed 1: Tunde Balogun's successful 2-day Severe Malaria admission
    cur.execute("""
        INSERT INTO short_stay_admissions (
            patient_id, provider_id, clinician_name, bed_number, admission_type, admission_reason,
            admitted_at, discharged_at, status, daily_ward_notes, discharge_summary
        ) VALUES (
            'PHC-PT-005', 'PHC/26/NUR/103', 'Nurse Folake Adeyemi', 'Observation Bed 02',
            'Short-Stay (2 Days)',
            'Severe Malaria with recurrent vomiting, high pyrexia (39.5°C), and severe dehydration requiring IV Artesunate and fluid resuscitation',
            ?, ?, 'Discharged',
            'Day 1: Received IV Artesunate 120mg at 0, 12, 24 hrs + 1L Normal Saline. Temperature settled to 37.8°C. Vomiting stopped.\nDay 2: Tolerating oral fluids well. Afebrile for 18 hours.',
            'Patient recovered clinically. Switched to oral Artemether-Lumefantrine course. Discharged home in stable condition.'
        )
    """, ((datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
          (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))

    # Seed 2: Baby Aisha Bello's extended inpatient nutritional rehabilitation admission (18 Days active, up to 30-40 days)
    cur.execute("""
        INSERT INTO short_stay_admissions (
            patient_id, provider_id, clinician_name, bed_number, admission_type, admission_reason,
            admitted_at, discharged_at, status, daily_ward_notes, discharge_summary
        ) VALUES (
            'PHC-PT-009', 'PHC/26/MED/001', 'Dr. Kemi Sanni', 'Observation Bed 01',
            'Extended PHC Admission (18 Days Active - Nutritional Rehab)',
            'Severe Acute Malnutrition (MUAC 11.2cm, bilateral pitting pedal edema, persistent watery diarrhea) requiring inpatient therapeutic feeding protocol',
            ?, NULL, 'Active',
            'Day 1-7: Stabilization phase on F-75 therapeutic milk formula. Diarrhea controlled with Zinc & ORS.\nDay 8-14: Transitioned to Ready-to-Use Therapeutic Food (Plumpy''Nut). Edema resolved.\nDay 18: Child alert, gaining weight (6.8kg -> 7.4kg), MUAC improved to 11.8cm (Yellow band). Continuing daily feeding monitoring.',
            NULL
        )
    """, ((datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d %H:%M:%S"),))

    # 5. Referrals Table (Official Letter Transfer to Secondary Hospitals)
    cur.execute("""
        CREATE TABLE referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            referred_by VARCHAR,
            provider_id VARCHAR,
            clinician_name VARCHAR,
            destination_facility VARCHAR,
            urgency VARCHAR,
            reason TEXT,
            status VARCHAR DEFAULT 'Referred',
            transfer_vitals VARCHAR,
            counter_referral_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed Musa Ibrahim's emergency orthopedic referral to UCH Ibadan
    cur.execute("""
        INSERT INTO referrals (
            patient_id, referred_by, provider_id, clinician_name, destination_facility, urgency, reason,
            status, transfer_vitals, counter_referral_notes, created_at
        ) VALUES (
            'PHC-PT-007', 'PHC/26/MED/001', 'PHC/26/MED/001', 'Dr. Kemi Sanni',
            'University College Hospital (UCH) Ibadan',
            'Emergency Transfer',
            'Motorcycle accident (okada). Severe pain and gross deformity of right lower limb. Physical exam confirms closed midshaft fracture of right tibia and fibula. Limb stabilized in posterior plaster splint. Needs orthopedic reduction and surgical management.',
            'In Transit',
            'BP: 130/84 mmHg, Pulse: 96 bpm, Temp: 36.8°C. IV Paracetamol 1g given.',
            'Receiving surgical team notified by ambulance dispatch. Patient en route to UCH Accident & Emergency.',
            ?
        )
    """, ((datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),))

    # 6. Clinical Notes Table
    cur.execute("""
        CREATE TABLE clinical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            provider_id VARCHAR,
            note_text TEXT,
            supersedes_note_id INTEGER,
            correction_reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Paper Intakes Table (Local Hybrid Digitization)
    cur.execute("""
        CREATE TABLE paper_intakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id VARCHAR,
            hospital_number VARCHAR,
            folder_number VARCHAR,
            transcribed_by VARCHAR,
            flagged_for_review INTEGER DEFAULT 0,
            review_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("WardVault Clinical Database Seeded: 10 Realistic Personas with Hospital Numbers!")

    # 8. Cryptographic Audit DB
    conn_audit = sqlite3.connect(AUDIT_DB)
    cur_audit = conn_audit.cursor()
    cur_audit.execute("DROP TABLE IF EXISTS audit_log")
    cur_audit.execute("""
        CREATE TABLE audit_log (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR,
            action VARCHAR,
            target_patient_id VARCHAR,
            reason VARCHAR,
            previous_hash VARCHAR,
            current_hash VARCHAR
        )
    """)

    prev_hash = "0" * 64
    payload = f"SYSTEM|SYSTEM_INIT|ALL|WardVault Primary Healthcare Gateway Genesis Block|{prev_hash}"
    gen_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    cur_audit.execute("""
        INSERT INTO audit_log (timestamp, user_id, action, target_patient_id, reason, previous_hash, current_hash)
        VALUES (CURRENT_TIMESTAMP, 'SYSTEM', 'SYSTEM_INIT', 'ALL', 'WardVault Primary Healthcare Gateway Genesis Block', ?, ?)
    """, (prev_hash, gen_hash))

    conn_audit.commit()
    conn_audit.close()
    print("WardVault Cryptographic Audit DB Initialized!")

if __name__ == "__main__":
    seed_database()
