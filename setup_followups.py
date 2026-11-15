import sqlite3
from datetime import datetime, timedelta

def setup():
    conn = sqlite3.connect("wardvault_clinical.db")
    c = conn.cursor()

    # 1. Create followup_calls table
    c.execute("""
        CREATE TABLE IF NOT EXISTS followup_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encounter_id INTEGER,
            patient_id TEXT NOT NULL,
            call_type TEXT NOT NULL,
            call_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            caller_name TEXT NOT NULL,
            phone_dialed TEXT NOT NULL,
            call_outcome TEXT NOT NULL,
            rescheduled_date TEXT,
            clinical_notes TEXT,
            doctor_status TEXT DEFAULT 'ON_DUTY'
        )
    """)

    # 2. Create scheduled_followups table
    c.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            followup_date TEXT NOT NULL,
            clinic_type TEXT NOT NULL,
            clinical_notes TEXT,
            attending_clinician TEXT DEFAULT 'Dr. Kemi Sanni, MBBS',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Seed scheduled appointments for realistic PHC care
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    in_3_days = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    in_5_days = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    past_due = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")

    # Check if scheduled_followups is empty
    count = c.execute("SELECT count(*) FROM scheduled_followups").fetchone()[0]
    if count == 0:
        seed_appointments = [
            ("HOSP-2026-008", today, "Hypertension & Chronic Care", "Fasting blood sugar check & 30-day Amlodipine refill review", "Dr. Kemi Sanni, MBBS"),
            ("HOSP-2026-005", today, "Diabetes Management", "Postprandial blood glucose check & Metformin tolerance assessment", "Dr. Kemi Sanni, MBBS"),
            ("HOSP-2026-002", tomorrow, "Child Immunization Clinic", "9-Month Measles 1 + Vitamin A drops & growth weight charting", "Nurse Folake Adeyemi"),
            ("HOSP-2026-006", tomorrow, "Postnatal & Infant Wellness", "6-Week maternal involution check, lochia assessment & exclusive breastfeeding", "Nurse Folake Adeyemi"),
            ("HOSP-2026-001", in_3_days, "ANC & Pregnancy Clinic", "34-Week routine checkup, fetal heart auscultation & birth plan confirmation", "Dr. Kemi Sanni, MBBS"),
            ("HOSP-2026-003", in_5_days, "ART Clinic & Viral Refill", "Quarterly TLD refill, adherence counseling & CD4 count schedule", "Amina Bello, CHEW"),
            ("HOSP-2026-004", past_due, "Severe Malaria Recovery", "Day 7 clearance check post-artesunate, repeat PCV hemoglobin check", "Dr. Kemi Sanni, MBBS"),
        ]
        for p_id, f_date, clinic, notes, doc in seed_appointments:
            c.execute("""
                INSERT INTO scheduled_followups (patient_id, followup_date, clinic_type, clinical_notes, attending_clinician)
                VALUES (?, ?, ?, ?, ?)
            """, (p_id, f_date, clinic, notes, doc))
        print(f"✅ Seeded {len(seed_appointments)} scheduled follow-ups.")

    # Check if followup_calls has seed sample
    call_count = c.execute("SELECT count(*) FROM followup_calls").fetchone()[0]
    if call_count == 0:
        c.execute("""
            INSERT INTO followup_calls (
                encounter_id, patient_id, call_type, call_timestamp, caller_name,
                phone_dialed, call_outcome, rescheduled_date, clinical_notes, doctor_status
            ) VALUES (
                1, 'HOSP-2026-008', 'APPOINTMENT_REMINDER', datetime('now', '-2 hours'), 'Nurse Folake Adeyemi',
                '08077665544', 'Appointment Confirmed', NULL, 'Called Chief Samuel Adele. Reminded of today''s 10:00 AM BP check. Patient confirmed he is on the way.', 'ON_DUTY'
            )
        """)
        c.execute("""
            INSERT INTO followup_calls (
                encounter_id, patient_id, call_type, call_timestamp, caller_name,
                phone_dialed, call_outcome, rescheduled_date, clinical_notes, doctor_status
            ) VALUES (
                NULL, 'HOSP-2026-005', 'DOCTOR_AWAY_CONTINGENCY', datetime('now', '-1 hour'), 'Amina Bello (CHEW)',
                '08099887766', 'Step-Down Care by Nurse Completed', NULL, 'Doctor was off-seat for emergency call. Patient arrived at PHC. Nurse Folake took vitals (BP 124/80, Sugar 112 mg/dL) and dispensed 1-month Metformin refill.', 'AWAY'
            )
        """)
        print("✅ Seeded sample call logs.")

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup()
