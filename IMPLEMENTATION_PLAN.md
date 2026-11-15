# WardVault PHC: Implementation Plan
## Clinical MVP Realignment: OpenMRS-Benchmark, 3-Color Clean UI, Hybrid Local Records & De-Noised Workstation

**Target:** Primary Healthcare Centres (PHCs) / Family Health Centres  
**Benchmark:** OpenMRS (NigeriaMRS) Comparison & Differentiators  
**Current Milestone:** Final 12-Hour Implementation-Ready MVP  
**Status:** **READY FOR REVIEW**

---

## 1. OpenMRS Research & Competitive Edge

### A. How OpenMRS Operates in Nigeria (NigeriaMRS / Festac)
- **Deployment Context:** In Nigeria, OpenMRS (customized as NigeriaMRS) is predominantly deployed in secondary and tertiary facilities (such as Festac / Amuwo Odofin) heavily funded by PEPFAR, CDC, and USAID specifically for **HIV/AIDS reporting** (NDR / National Data Repository, viral load tracking, and ART registries).
- **The OpenMRS Gap in Nigerian PHCs:**
  1. **Heavy Architecture:** OpenMRS runs on a heavy Java/Spring/Tomcat/MySQL stack requiring high-spec servers and constant technical maintenance. Underserved PHCs lack dedicated IT staff and server rooms.
  2. **Not Truly Offline-First:** OpenMRS was architected for connected client-server LANs. In rural and peri-urban PHCs with zero internet and frequent blackouts, OpenMRS instances fail or cannot sync reliably.
  3. **Complex EAV Schema:** The Entity-Attribute-Value database model with thousands of concept tables makes simple primary care reporting slow and over-engineered for community health extension workers (CHEWs).
  4. **Neglect of Routine Primary Care:** OpenMRS in Nigeria is rarely used for routine walk-in primary care (malaria, antenatal checkups, child immunization, hypertension refills). It is treated as a donor-compliance HIV tool.

### B. How WardVault Differentiates & Wins
- **Visual Simplicity:** Adopts the clean, un-crowded, non-noisy design philosophy of OpenMRS 3 (O3) without any flashy "AI-vibe" gradients or neon badges.
- **True Offline-First Local Node:** Runs natively on local low-power hardware (laptops, mini-PCs, tablets) using SQLite and browser IndexedDB. Operates 100% offline with zero latency.
- **Routine PHC Focus:** Built specifically for routine Nigerian Family Health Centre care: OPD (General Clinic), Antenatal Care (ANC), Child Immunization (EPI), Short-Stay Admissions, and Emergency Referrals.
- **Hybrid Paper/Digital:** Allows clinical staff to work with physical paper cards while data clerks digitize records seamlessly in the local environment.

---

## 2. UI De-Noising & 3-Color Palette

All "AI-ish" neon badges, pulsing telemetry widgets, theoretical explanation blocks, and multi-colored tabs are removed. The UI is restricted strictly to **three primary colors**:

1. **Deep Slate / Medical Navy (`#0f172a` / `#1e293b`):** For typography, structural sidebars, and clean headers.
2. **Clinical Blue / Teal (`#0284c7` / `#005b5b`):** For primary actions, active navigation items, and positive confirmations.
3. **Clean Neutral Gray / White (`#f8fafc` / `#ffffff`):** For high-contrast surfaces, clean tables, and subtle borders (`#e2e8f0`).
*(Subtle red `#dc2626` is reserved solely for medical safety alerts, such as drug allergies).*

---

## 3. Scope of Work (Exact Implementation Changes)

### 1. Patient Navigation & Registration Overhaul
- **Header Patient Action:** Remove the large bulky "+ Register New Patient" banner button. Replace it with a clean patient icon `👤+` in the header bar with a dropdown menu option: **"Add Patient"**.
- **New Patient Form Fields:**
  - Replace the `phone` field with **Hospital Number** (`hospital_number`, e.g., `HOSP-2026-0412`).
  - Keep clean essential demographics: First Name, Last Name, Age, Gender, Hospital Number, Clinic Classification (OPD General Clinic, ANC Maternity, Child Health / EPI).
- **Remove Orthopedic Cabinet:** Family health centres do not have orthopedic departments. The clinic cabinets are simplified to:
  1. `All Records`
  2. `OPD (General Clinic)`
  3. `ANC & Maternity`
  4. `Child Health & Immunization (EPI)`
  *(Orthopedic trauma cases like Musa Ibrahim present to OPD and are immediately stabilized and referred to secondary hospitals).*

### 2. Multi-Test Laboratory Investigation Dropdown
- Replace the previous freeform text and malaria-only radio buttons with a **multi-test selector dropdown** containing standard Nigerian PHC laboratory and diagnostic investigations:
  - Malaria Rapid Diagnostic Test (mRDT)
  - Genotype (Hb Electrophoresis: AA, AS, SS, AC)
  - Fasting / Random Blood Sugar
  - H. pylori Rapid Antigen Test
  - Packed Cell Volume (PCV / Hemoglobin)
  - Urinalysis (10-Parameter Dipstick)
  - Obstetric / Abdominal Ultrasound Scan
  - Chest / Extremity X-Ray
  - Sputum AFB / GeneXpert (Tuberculosis)
  - HIV 1/2 Rapid Screening
- Clinicians can select any test, record findings or mark as ordered, and attach multiple investigations to the consultation cleanly.

### 3. Consultation Flow & Single-Line Visit History (OpenMRS Style)
- **Consultation Order Maintained:** History (Reason for visit) $\rightarrow$ Examination & Entry Vitals $\rightarrow$ Investigations (Test dropdown) $\rightarrow$ Diagnosis $\rightarrow$ Prescription (Rx) $\rightarrow$ Clinical Outcome.
- **De-Noised Single-Line Visit History:**
  - Replace multi-layered noisy cards with clean single-line table rows dated and showing the attending clinician's name:
    | Date & Time | Visit Type | Attending Clinician / Doctor | Diagnosis / Findings | Outcome | Action |
  - Clean modal / expand drawer to view consultation details without clutter.
- **Past Visit Readings Table:** Retain the stacked chronological blood pressure comparison table for returning chronic patients (Chief Samuel Adele: `160/98` $\rightarrow$ `142/90` $\rightarrow$ `126/82`) formatted in clean, uncrowded monochrome.

### 4. Observation & Admission Ward (Short Stays to 30–40 Days)
- Support both:
  - **Short-Stay Admissions (1–3 Days):** Severe malaria on IV Artesunate, acute dehydration rehydration, labor observation.
  - **Extended PHC Admissions (up to 30–40 Days):** Nutritional rehabilitation for severe acute malnutrition (e.g. Baby Aisha Bello on therapeutic feeding), chronic wound management, and prolonged primary recovery.
- Ward Bed management with Bed Number, Admission Date, Attending Doctor, Daily Progress Notes, and Discharge Summary.

### 5. Official Letter Transfer Slip with Back Button
- **Clear Navigation:** Add a prominent **"← Back to Referrals"** button and close button so staff can close the slip immediately without refreshing the page.
- **Official Letter Format:** Format the slip as a formal medical referral letter from Alakia Primary Healthcare Centre addressed to the receiving secondary hospital (e.g. University College Hospital UCH Ibadan).
- **Remove Digital Hash Clutter:** Strip raw cryptographic hash text strings (`WARDVAULT-DIGITAL-SIGNATURE-...`) from the printable document. Replace with a formal medical sign-off:
  ```
  Dr. Kemi Sanni, MBBS, MPH
  Medical Officer in Charge, Alakia Primary Healthcare Centre
  Egbeda Local Government Area, Oyo State
  [Official Stamp & Signature]
  ```

### 6. Hybrid Paper-to-Digital Care (Local Storage)
- Drop theoretical 3-layer architecture diagrams and lengthy explanatory paragraphs.
- Keep the system purely functional:
  - Records staff digitize physical paper cards directly into local storage.
  - Data is saved directly in the local environment (`wardvault_clinical.db` via SQLite and browser IndexedDB).
  - Works with or without network access (hybrid fallback).

---

## 4. Work Breakdown & Execution Steps

1. **Step 1: Database & Seed Realignment (`seed_phc_mvp.py` & `main.py`)**
   - Update `patients` table to ensure `hospital_number` is first-class.
   - Remove orthopedic clinic tag; map trauma patient Musa Ibrahim to OPD with emergency secondary referral to UCH.
   - Support extended admissions up to 30–40 days in `short_stay_admissions`.
   - Update `clinical_encounters` investigations to store structured test lists from dropdown.

2. **Step 2: Backend API Routes (`main.py`)**
   - Update patient registration model to accept `hospital_number`.
   - Update referral slip payload to produce the clean, formal medical letter format without raw hash strings.
   - Ensure all endpoints return clean, concise responses.

3. **Step 3: Frontend Interface Redesign (`index.html`)**
   - Apply 3-color palette (Deep Slate, Clinical Blue/Teal, Neutral White/Gray).
   - Implement header `👤+` icon with "Add Patient" dropdown.
   - Replace phone field with Hospital Number in patient registration.
   - Implement multi-test investigation dropdown (mRDT, Genotype, Blood Sugar, H. pylori, PCV, Urinalysis, Ultrasound, X-Ray, TB, HIV).
   - Convert past visit history into OpenMRS-style single-line dated rows with attending doctor's name.
   - Refactor Transfer Slip into an official letter with a functional **"← Back to Referrals"** button and clean close actions.
   - Simplify Paper/Digital tab into a clean, practical local digitizer without theoretical essays.

4. **Step 4: Verification & Deployment**
   - Run `test_api.py` and verify all endpoints pass.
   - Test UI in browser at `http://127.0.0.1:8000/`.
   - Commit and push to `origin main` for automated Render deployment.

---

> **Ready for User Review:** This implementation plan focuses strictly on the current active scope. Once reviewed, implementation will proceed immediately.
