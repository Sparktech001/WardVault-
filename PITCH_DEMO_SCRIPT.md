# 🏆 WardVault PHC: 3-Minute Pitch & Live Clinical Demo Script

**Competition:** Universal Service Provision Fund (USPF) Changemaker Challenge 2026  
**Track:** Healthcare Innovation / PHC Technology Resilience  
**Live Target:** Implementation-Ready PHC MVP (Offline Local Node + Secondary Referral Gateway)

---

## ⏱️ Minute 1: The Problem & The Paper Reality (60 seconds)

### What to Say:
> *"Good day, distinguished panel. In Nigeria, the 2026 Tech Outlook Report published by NITDA and the National Bureau of Statistics surveyed over 500 Primary Healthcare Centres. The reality on the ground is stark:*
> - *Only **16.2%** of PHCs have reliable internet connectivity.*
> - *Over **38%** suffer from frequent power blackouts.*
> - *And over **73%** still rely entirely on physical paper folders.*
>
> *Most digital health systems fail at PHCs because they try to force complex, tertiary hospital software into rural facilities. They overwhelm community nurses with academic jargon, require high-speed internet, and break down because there is no staged transition from physical paper charts.*
>
> *Introducing **WardVault**: The implementation-ready, offline-first Primary Healthcare workstation designed to mirror standard paper clerkship, manage short-stay observation beds, coordinate emergency referrals to secondary hospitals, and transition paper folders in three safe layers."*

---

## ⏱️ Minute 2: The Live Demonstration (75 seconds)

### Actions to Perform on Screen:

#### 1. Sign In via Realistic Staff Role:
- Click the quick button for **Nurse Folake** (`PHC/26/NUR/103`) or **Amina Bello (CHEW)** (`PHC/26/CHEW/102`).
- Click **Sign In to Clinical Station**.
- *Say:* *"Notice that our interface speaks plain clinic language. No academic buzzwords like 'OPD' or 'triage encounters'—only everyday terms PHC staff use: General Clinic, ANC, Child Immunization, and Observation Ward."*

#### 2. Open Patient Records & Filing Cabinets:
- In the **Patient Records** tab, show the 5 clinic cabinet drawers:
  - 🗂️ **All Records (10)**
  - 🤰 **ANC & Pregnancy**
  - 🩺 **General Clinic**
  - 👶 **Child & Immunization**
  - 🦴 **Orthopedic & Injury**
- Demonstrate the **A–Z Quick Jump Bar**: Click letter **'S'** to instantly find **Chief Samuel Adele**, or click letter **'A'** for **Amina Garba**.
- *Say:* *"Records officers can filter by clinic department or instantly jump alphabetically by first name or surname in milliseconds."*

#### 3. Demonstrate Returning Patient Vitals Trend (Chief Samuel Adele):
- Click **Open Consultation 🩺** on **Chief Samuel Adele** (`CHRONIC-2026-08`).
- Point to the **Past Visit Readings Table**:
  - Show the 3 stacked chronological blood pressure readings:
    - *3 Months Ago:* `160/98 mmHg` (Uncontrolled Stage 2)
    - *1 Month Ago:* `142/90 mmHg` (Suboptimally Controlled)
    - *Recent Refill:* `126/82 mmHg` (Controlled glycemic & BP response)
- *Say:* *"Here is clinical panel feedback delivered: For returning chronic care patients, the nurse does not hunt through pages of old notes. All previous blood pressure readings appear together chronologically, immediately showing if the medication is working."*

#### 4. The 6-Step Paper-Mirroring Consultation Clerkship:
- Walk down the 6 standard clerkship steps:
  1. **History:** Reason for visit / chief complaint.
  2. **Physical Exam & Entry Vitals:** Entry BP, Temperature, Pulse, Weight, Blood Sugar.
  3. **Point-of-Care Tests:** Malaria mRDT, PCV, Blood Sugar, Urinalysis.
  4. **Diagnosis & Differentials:** Primary working diagnosis and alternative conditions.
  5. **Prescription (Rx):** Medication dosing and lifestyle counseling.
  6. **Clinical Outcome:** 5 clear pathways: *Give Drugs & Go Home*, *Order Tests & Return*, *Book Next Visit*, *Admit to Observation Bed*, or *Transfer Patient*.
- *Say:* *"Our consultation follows the exact order clinicians were taught in school: History, Examination, Tests, Diagnosis, Drugs, and Outcome."*

#### 5. Short-Stay Observation Ward (1 to 3 Days):
- Click the **Observation Ward** tab.
- Show active beds and the completed 2-day recovery case for **Tunde Balogun** (admitted for Severe Malaria on IV Artesunate and fluid resuscitation, then discharged afebrile).
- Click **+ Add Ward Progress Note** to append a timestamped observation.
- *Say:* *"PHCs are not just outpatient desks. Patients with severe malaria or dehydration are admitted for 24 to 72 hours for IV therapy before discharge or escalation."*

#### 6. Secondary Referral & Official Printable MOH Transfer Slip:
- Click the **Hospital Transfers** tab.
- Show **Musa Ibrahim** (`PHC-PT-007`): Closed tibia fracture from motorcycle crash requiring emergency orthopedic transfer to **University College Hospital (UCH) Ibadan**.
- Click **🖨️ Print Official Transfer Slip**.
- The print modal opens showing the official **Federal Republic of Nigeria Primary Healthcare Referral Slip** with facility MOH code (`OY/EGB/PHC-04`), pre-transfer vitals, emergency splinting notes, and the cryptographic digital seal (`WARDVAULT-DIGITAL-SIGNATURE-...`).
- *Say:* *"When emergencies exceed PHC capacity, WardVault issues a legally compliant secondary transfer slip and tracks the patient from ambulance dispatch to counter-referral."*

---

## ⏱️ Minute 3: Resilience, Staged Migration & NDPA Trust (45 seconds)

### Actions to Perform on Screen:

#### 1. 3-Layer Paper-to-Digital Migration:
- Click the **Staged Migration** tab.
- Explain the 3 layers:
  - **Layer 1 (Digital-First):** New patients and newborns register 100% digital.
  - **Layer 2 (Parallel Dual-Track):** Existing patients run paper and digital in parallel with zero clinic disruption.
  - **Layer 3 (Archival Catch-Up):** Old folders transcribed off-peak; faded or illegible entries are flagged for nurse review before permanent archival.

#### 2. Offline Resilience & Battery Power Alarm:
- Click the battery telemetry badge in the top navbar to simulate battery depletion from 100% $\rightarrow$ 80% $\rightarrow$ 20%.
- Toggle the power plug icon to simulate grid failure.
- *Say:* *"WardVault works fully offline with local IndexedDB storage. In a power outage, it alerts the nurse before battery failure so solar backup can be connected."*

#### 3. Cryptographic SHA-256 Ledger:
- Point out the **SHA-256 Chained** badge.
- *Say:* *"Every encounter, admission note, and transfer is chained into an immutable SHA-256 cryptographic ledger, ensuring full compliance with the Nigeria Data Protection Act (NDPA) 2023."*

---

## 🎯 Winning Closing Statement (15 seconds)

> *"WardVault does not ask Nigerian PHCs to wait for universal fiber internet or 24/7 power that may take years. We meet primary healthcare workers where they are today: with offline-first reliability, paper-mirroring clinical clerkship, short-stay observation beds, closed-loop secondary referrals, and staged paper transition.*
>
> *Thank you, and we welcome your questions."*
