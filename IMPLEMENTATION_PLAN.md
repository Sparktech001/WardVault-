# WardVault: 12-Hour PHC Implementation MVP Plan
## Implementation-Ready Patient Records & Care-Coordination Platform for Underserved Nigerian PHCs

**Target Track:** USPF Changemaker Challenge 2026 (Track C: Healthcare Innovation)  
**Target Setting:** Underserved Primary Healthcare Centres (PHCs) across Nigeria  
**Product Framing:** Implementation-Ready MVP (Designed for real clinical adoption, not an abstract prototype)  
**Status:** **AWAITING USER CONFIRMATION & APPROVAL (No code changes applied yet)**  

---

## 1. Executive Summary & Synthesis of Team Review

Following the team lead, panel, and speaker review, WardVault is being tailored specifically for **Nigerian Primary Healthcare Centre reality**. 

PHC nurses and Community Health Extension Workers (CHEWs) do not use tertiary hospital electronic systems; they work with **standard paper folders**, face frequent power outages, handle **short-stay admissions (1–3 days)** for acute illnesses like severe malaria, and require **plain, intuitive everyday language** rather than developer jargon or AI-sounding buzzwords.

---

## 2. Plain Language UI Dictionary (Removing Technical Jargon)

To ensure nurses, CHEWs, and records officers feel immediately at home, all academic and tertiary hospital jargon will be replaced with plain, practical clinic words:

| Jargon to REMOVE | Plain Language Replacement | Why the Change Matters |
| :--- | :--- | :--- |
| **OPD / Outpatient** | **General Clinic** or **Daily Patients** | PHC staff and patients call general consultations the "General Clinic". |
| **Longitudinal Vitals** | **Past Visit Readings** | Plain description of previous blood pressure and temperature checks. |
| **Paper Migration Review Queue** | **Register Existing Paper Folder** | Clear action for entering an old physical folder into the system. |
| **ABAC Policy Restriction** | **Staff Member Off-Duty** | Clean notice explaining that staff must be on shift to access records. |
| **Triage Encounter** | **Patient Consultation** | Mirrors the physical consultation room. |
| **Chief Complaint** | **What brought the patient today?** | Natural medical interview question used in primary care clerkship. |
| **Cryptographic Hash Proof** | **Verified Clinic Record ✓** | Assures staff the record is locked and tamper-evident without confusing math terms. |

---

## 3. The 10 Real-World Sample Patients (Curated MVP Cohort)

The 100+ generic synthetic entries (`FL-1000` series) will be completely replaced with **10 realistic, diverse clinical cases** based on daily Nigerian PHC practice:

| # | Patient Name | Age / Sex | Clinic Folder # | Clinical Story & Management |
| :- | :--- | :--- | :--- | :--- |
| **1** | **Amina Garba** | 26 / F | **ANC-2026-01** | **Pregnancy & Delivery (ANC):** 32 weeks pregnant. Normal blood pressure (115/75), fundal height matches dates. Given Iron/Folic acid and second dose of Fansidar (IPTp) to prevent malaria. Booked for next check in 2 weeks. |
| **2** | **Baby Kazeem Adeleke** | 6 wks / M | **EPI-2026-02** | **Newborn Immunization:** 6-week routine immunization visit. Received Pentavalent 1, Oral Polio 1, PCV 1, and Rotavirus 1. Weight: 4.3kg. Mother counseled on exclusive breastfeeding. |
| **3** | **Joy Okafor** | 34 / F | **GEN-2026-03** | **HIV Regular Drug Pickup:** Known HIV patient doing well on TLD daily tablets. Undetectable viral load. Given 3-month drug refill, checked for side effects, adherence confirmed. |
| **4** | **Usman Danladi** | 42 / M | **GEN-2026-04** | **Tuberculosis (TB) Care:** Coughing for over 3 weeks with night sweats and weight loss. Sputum test ordered; started on standard 4-drug Anti-TB fixed-dose combination (RHZE). Contact tracing initiated. |
| **5** | **Tunde Balogun** | 19 / M | **GEN-2026-05** | **Severe Malaria (Admitted for 2 Days):** Arrived with high fever (39.5°C), vomiting, and extreme weakness. Rapid malaria test positive. **Admitted to Observation Ward** for IV Artesunate and IV fluids for 36 hours. Recovered, completed oral ACT, and discharged home. |
| **6** | **Blessing Adeleke** | 29 / F | **GEN-2026-06** | **Depression / Mental Health:** Mother of young child presenting with 2 months of constant crying, exhaustion, lack of sleep, and feelings of hopelessness. Screened with PHQ-9 (moderate depression). Given supportive counseling and scheduled for weekly support. |
| **7** | **Musa Ibrahim** | 35 / M | **ORTHO-2026-07** | **Orthopedic / Bone Injury (Referral):** Okada motorcycle rider involved in a crash. Broken right lower leg bone (closed tibia fracture). Leg splinted, given pain relief, and given an **Emergency Secondary Transfer Slip to UCH Ibadan**. |
| **8** | **Chief Samuel Adele** | 58 / M | **CHRONIC-2026-08** | **High Blood Pressure & Diabetes:** Long-standing hypertension. Today's BP: 155/95 mmHg. Fasting blood sugar: 180 mg/dL. Past visit readings show gradual improvement. Refilled Amlodipine 10mg and Metformin 500mg. Counseled on salt reduction. |
| **9** | **Baby Aisha Bello** | 14 mos / F | **EPI-2026-09** | **Child Malnutrition & Diarrhea:** Weak toddler with watery stool. Arm tape check (MUAC) shows 11.2 cm (Red - Severe Wasting). Started immediately on ORS, Zinc, and Plumpy'Nut (RUTF paste). |
| **10** | **Emmanuel Chukwu** | 7 yrs / M | **GEN-2026-10** | **Routine Child Health & Deworming:** Healthy primary school boy. Given Albendazole 400mg tablet to clear stomach worms and Vitamin A capsule for healthy eyes. |

---

## 4. Consultation Flow: Following the Physical Paper Folder

The consultation screen will be structured in the exact step-by-step order of the standard physical paper clerkship:

```
[ Step 1: PATIENT HISTORY ]
  - What brought the patient today? (Main complaint & duration, e.g. "3 days of hot body and shivering")
  - Details of illness (History of Presenting Complaint)
  - Past medical history, current drugs, and allergies

[ Step 2: PHYSICAL EXAMINATION ]
  - Today's Vital Signs (Blood pressure, Temperature, Pulse, Weight)
  - Physical Observations (Pallor/pale eyes, dehydration, swollen feet, chest sounds, abdomen)

[ Step 3: TESTS & INVESTIGATIONS ]
  - Point-of-care clinic tests:
    * Malaria Rapid Test (mRDT): Negative / Positive
    * Sputum Test for TB
    * HIV Rapid Screening
    * Urinalysis & Blood Sugar test

[ Step 4: DIAGNOSIS ]
  - Main Diagnosis (e.g., Severe Malaria, Gestational Anemia, Bone Fracture)
  - Other possible conditions (Differential diagnoses)

[ Step 5: TREATMENT & PRESCRIPTION (Rx) ]
  - Prescribe medicines (Drug name, dose, times per day, how many days)
  - Pharmacy dispensing notes

[ Step 6: CONSULTATION OUTCOME ]
  1. Give Drugs & Go Home (Outpatient discharge)
  2. Order Tests & Return (Wait for clinic lab results today)
  3. Book Next Visit (e.g., return in 2 weeks for BP check or 3 months for HIV drugs)
  4. ADMIT TO OBSERVATION WARD (1 to 3 Days short-stay admission)
  5. TRANSFER PATIENT (Secondary Referral to General Hospital / Teaching Hospital)
```

---

## 5. Short-Stay Admission Flow (1 to 3 Days)

Primary healthcare centres do not have large surgical wards, but they **routinely admit patients for 1 to 3 days** (Observation Beds) for:
- Severe malaria on IV Artesunate / drips
- Dehydrated children receiving IV/oral rehydration
- Women in early labor / post-delivery observation (24 hours)

### How the Admission Flow Works:
1. **Admit Action:** Clinician selects **"Admit to Observation Ward (1–3 Days)"**, chooses an observation bed (e.g. Bed 02), and notes admission reason.
2. **Observation Ward List:** A dedicated tab shows currently admitted patients in the facility with their length of stay (e.g. *Tunde Balogun • Admitted 24 hrs ago • Bed 02*).
3. **Daily Ward Notes:** Nurses log daily progress notes and morning/evening vitals without having to register a whole new patient.
4. **Resolution:** Clinician selects either:
   - **Discharge Home** (condition resolved, switch to oral tablets)
   - **Transfer to General Hospital** (patient not improving, escalate referral).

---

## 6. Past Visit Readings (Blood Pressure & Vitals History)

When a returning patient is opened in the consultation room, the clinician sees all previous visit readings arranged together chronologically:

| Visit Date | Blood Pressure | Temp | Pulse | Weight | Clinical Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Today** | **126 / 82 mmHg** (Controlled) | 36.8°C | 74 bpm | 75.5 kg | Responding well to Amlodipine |
| **1 Month Ago** | **142 / 90 mmHg** (High Stage 1) | 36.7°C | 78 bpm | 76.0 kg | Dose adjusted to 10mg |
| **3 Months Ago** | **160 / 98 mmHg** (High Stage 2) | 37.0°C | 84 bpm | 78.2 kg | Initial presentation with headaches |

Staff can immediately tell if blood pressure is improving without digging through stacks of archived papers.

---

## 7. Staged Paper-to-Digital Migration (Three Layers)

Instead of an arbitrary review flag, migration is designed around real facility operations to prevent lines and duplicate records:

*   **Layer 1: Digital-First for New Patients**  
    Any patient arriving at the PHC for the first time is entered directly into WardVault. No paper chart is created.
*   **Layer 2: Dual-Track for Existing Paper Folders**  
    When a returning patient arrives with an old paper card, the Records Officer enters their existing folder number (e.g. `ANC-042`) and basic demographics. The paper folder continues to serve as the physical legal record while current consultations run digitally in parallel.
*   **Layer 3: Archival Catch-Up (Off-Peak Hours)**  
    Records staff transcribe older paper chart histories during quiet afternoon hours so morning clinic queues are never kept waiting.

---

## 8. Fully Functional Closed-Loop Referral System

To turn the current frontend mockup into a working clinical referral tool:
1. **Real Database Backend:** A dedicated `referrals` table records patient ID, referring officer, destination hospital (e.g., *University College Hospital UCH Ibadan*, *Adeoyo Maternity*, *General Hospital Oyo*), clinical reason, urgency, and transfer notes.
2. **Official Transfer Slip (Printable/Saveable):** One-click button generates a standard Nigerian PHC Referral Transfer Slip formatted cleanly with clinical summary, transfer vitals, and provisional diagnosis.
3. **Care Loop Stepper:** Tracks the referral from **Initiated at PHC → In Transit → Received at Hospital → Feedback Received & Closed**.

---

## 9. Login Roles & Facility Access

Clean, realistic staff roles for the demo:
1. **Staff Midwife / Nurse** (`PHC/26/NUR/103` • Nurse Folake) — Consultations, ANC, deliveries, admissions.
2. **Community Health Extension Worker (CHEW)** (`PHC/26/CHEW/102` • Amina Bello) — Triage, malaria, vaccinations, general clinic.
3. **Records Officer** (`PHC/26/REC/101` • Ibrahim Musa) — Folder registration, paper-to-digital indexing.
4. **Facility In-Charge (Chief)** (`PHC/26/MED/001` • Dr. Kemi Sanni) — Oversight, approvals, referral escalation, facility reports.

---

## 10. Execution Plan (What We Will Build)

- [ ] **Step 1: Database Seed Overhaul (`database.py`, `restore_dataset.py`)**
  - Clear out the generic 100+ Synthea rows and seed the exact 10 realistic PHC patients.
  - Create the `short_stay_admissions` table for 1–3 day observation beds.
  - Seed historical visit vitals (past BP readings) for returning patients.
- [ ] **Step 2: Backend API Routes (`main.py`)**
  - Add routes for Short-Stay Admissions: `POST /api/admissions`, `GET /api/admissions/active`, `PATCH /api/admissions/{id}/discharge`.
  - Update `POST /api/encounters` to save structured paper clerkship fields (History, Exam, Tests, Diagnosis, Rx, Outcome).
  - Connect full referral management with transfer slip data endpoint.
- [ ] **Step 3: Frontend UI Redesign (`index.html`)**
  - Simplify all labels into plain language (General Clinic, Past Visit Readings, etc.).
  - Build the paper-style consultation room (History → Exam → Tests → Diagnosis → Rx → Outcome).
  - Add the **Short-Stay Observation Ward** tab (1–3 days admissions).
  - Add the **Past Visit Readings** historical vitals table for returning patients.
  - Make referral status updates and printable transfer slips fully functional.
- [ ] **Step 4: Verification & Git Deployment**
  - Run automated API tests on all 10 clinical scenarios and admissions.
  - Push to GitHub `main` for instant Render cloud deployment.

---

## 11. Approval & Confirmation Gate

> **No code has been altered yet.**  
> Please review this updated implementation plan. Once you give your confirmation, we will begin implementation and deliver the completed, plain-language MVP.
