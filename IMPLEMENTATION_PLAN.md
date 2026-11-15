# WardVault: USPF Changemaker Challenge Strategic Implementation Plan

**Target Track:** Healthcare Innovation for Underserved Communities  
**Product Positioning:** *Offline-First Patient Records & Care-Coordination Platform for Primary Healthcare Centres (PHCs)*  
**Author:** Pair Programming Strategy Team  
**Status:** Awaiting User Confirmation & Approval (No Code Changes Applied Yet)

---

## 1. Executive Summary & Deployment Feasibility

### Yes, We Can Make It Work and Deploy It!
**Yes, 100%.** Not only will we make the local application fully functional, but we will also prepare it for **dual deployment**:

```
[Local PHC Facility Deployment (Offline LAN)]
  CHEW Tablet (Wi-Fi) -----\
  Nurse Laptop (LAN) -------> [ PHC Gateway (Local Laptop/Mini-PC) ]
                                    |
                            [ Encrypted Local SQLite DB ]
                            [ Pending Sync Queue ]
                                    | (Auto-Sync when Internet/Cellular returns)
                                    v
[Cloud Live Deployment (Render/Railway/Vercel)]
  Remote Judges / Web Evaluators ---> [ WardVault Cloud Gateway & Central Ledger ]
```

1. **Live Web Deployment (Cloud):** Deployed to Render / Railway / Vercel so the USPF judging panel, partners, and team members can test the system immediately in any browser with zero setup.
2. **Local Facility Deployment (Offline LAN):** Packaged to run on an inexpensive facility laptop or mini-PC acting as the local server over a basic Wi-Fi router, providing complete offline capability across tablets without needing internet access.

---

## 2. Competitive Alignment (Why WardVault Wins)

The 2026 NITDA & NBS Tech Outlook Report reveals that **only 16.2% of Nigerian PHCs have working internet**, and **only 26.4% keep electronic records**. 

| Dimension | Helium Health | OpenMRS | **WardVault (Proposed)** |
| :--- | :--- | :--- | :--- |
| **Target Setting** | Large private/tertiary hospitals | General low-resource clinics | **Individual Underserved PHCs** |
| **Offline Reality** | Cloud-dependent ecosystem | Requires heavy server infrastructure | **Lightweight local LAN + IndexedDB queue** |
| **Paper Migration** | Software only; facility must solve | Self-managed / custom | **Managed Paper-to-Digital intake workflow** |
| **Power Instability** | Unaddressed by software | Unaddressed by software | **Built-in battery & power-loss detection alerts** |
| **Data Integrity** | Standard DB logs | Standard DB audit | **Cryptographic SHA-256 chained ledger (NDPA 2023)** |
| **Care Coordination** | Complex multi-facility tools | Complex referral modules | **Streamlined PHC-to-Secondary referral tracker** |

---

## 3. What We Are KEEPING (Existing Assets)

We do **not** throw away your existing hard work. We leverage the core security and cryptographic middleware that made WardVault strong in Track C:

1. **FastAPI Gateway Engine & Dual-DB Architecture:**
   - Keep the clean asynchronous FastAPI backend.
   - Keep the dual SQLite/PostgreSQL layer (runs instantly on SQLite locally; can scale to Postgres in the cloud).
2. **Cryptographic SHA-256 Audit Ledger (`audit_service.py`):**
   - Keep the blockchain-style hash chain (`user_id|action|patient_id|reason|previous_hash`).
   - This provides undeniable proof of compliance with the **Nigeria Data Protection Act (NDPA) 2023**.
3. **Append-Only Clinical Note Amendments (`main.py`):**
   - Keep the `supersedes_note_id` correction flow so clinical observations cannot be retroactively erased or forged.
4. **Offline Storage Engine & Sync Logic (`index.html` `WardVaultDB`):**
   - Keep the IndexedDB local database and queue for pending records.
5. **Hardware Battery & Power Loss Detection (`index.html`):**
   - Keep the Battery API status indicators and audio alerts that notify healthcare workers when external AC power is cut.
6. **Synthea Synthetic Patient Records:**
   - Keep the 278 staff and 113 patient records to demonstrate realistic healthcare scenarios without violating privacy laws.

---

## 4. What We Are SUBTRACTING (Hospital Jargon to Remove)

To tailor the system specifically for a Primary Healthcare Centre rather than a tertiary teaching hospital:

1. **Subtract Inpatient Ward Isolation (`uch-cardiology`, `uch-surgery`, `uch-icu`):**
   - *Reason:* PHCs are primary outpatient clinics. They do not have specialized cardiology or surgical wards. Locking records by specialized ward causes confusion in a primary clinic where a single nurse or CHEW handles all outpatients.
2. **Subtract Doctor "Break-Glass" Emergency Override:**
   - *Reason:* Break-glass was built for ER/ICU doctors. PHCs are staffed by Community Health Extension Workers (CHEWs), midwives, and primary care nurses.
3. **Subtract Complex Cross-Tenant Hospital Isolation (UCH vs JAJA):**
   - *Reason:* Reframe the multi-tenant model. Instead of two large competing tertiary hospitals, the system is designed around **one PHC** that coordinates outbound referrals to secondary/tertiary facilities.
4. **Subtract Tertiary Administrative Roles (e.g., "Billing Clerk", "IT Admin"):**
   - *Reason:* In rural PHCs under BHCPF (Basic Health Care Provision Fund), primary care is community-oriented. Roles should reflect real PHC staff: **Records Officer**, **Nurse / Midwife**, and **CHEW**.

---

## 5. What We Are ADDING (New PHC Capabilities)

### A. Structured Paper-to-Digital Intake Mode
*   **Dedicated Intake Interface:** Allows records officers to rapidly transcribe historical paper folders into digital records.
*   **Safe Handling of Illegible Notes:** A one-click checkbox: *"Flag Illegible for Clinical Review"* so data-entry staff never guess handwriting or invent clinical data.
*   **Key PHC Identifiers:** Support for National ID (NIN), BHCPF ID, and legacy Paper Folder Number.

### B. Outpatient Clinical Encounter & Vitals Workflow
*   **Simplified Primary Care Form:** Tailored for the most common PHC presentations in Nigeria:
    - Malaria screening (RDT results)
    - Antenatal Care (ANC) & Maternal Health
    - Routine Childhood Immunizations
    - Hypertension & Diabetes screening
*   **Vital Signs Triage:** Quick recording of Blood Pressure, Temperature, Pulse, and Weight.

### C. Referral & Follow-up Coordination Engine
*   **Outbound Referral Generator:** Generates a standard transfer slip from the PHC to a designated General Hospital or Federal Medical Centre.
*   **Follow-up Tracker:** The PHC tracks:
    - *Referral Status:* Referred -> Attended Secondary Facility -> Feedback Received -> Care Completed.

### D. Offline Conflict Resolution & Sync Queue
*   **Version Timestamps:** When multiple tablets record notes offline, the local gateway merges records cleanly based on patient ID and timestamp, preventing accidental overwrites.
*   **Sync Health Monitor:** A clear visual indicator showing how many records are stored locally and waiting to be backed up to the cloud.

### E. NDPA 2023 Consent & Compliance Record
*   **Explicit Patient Consent Check:** Logged into the cryptographic audit trail for handling health data.

---

## 6. Implementation Roadmap & Phases

- **Phase 1: Backend & Schema Alignment**
  - Update roles to: `Records Officer`, `Nurse`, `CHEW`, `Facility In-Charge`.
  - Add models for `OutpatientEncounter`, `Referral`, and `PaperIntake`.
  - Retain SHA-256 cryptographic chaining on all new event types.
- **Phase 2: Frontend Workflow Upgrades**
  - Build the **Paper Migration Mode** interface.
  - Build the **Primary Care Outpatient Encounter** form.
  - Build the **Referral & Follow-up Management** dashboard.
- **Phase 3: Offline Resilience & Conflict Resolution**
  - Verify offline IndexedDB operations without active Wi-Fi.
  - Ensure automatic sync resumes as soon as connection is re-established.
- **Phase 4: Cloud Deployment & Pitch Readiness**
  - Configure production Dockerfile or direct cloud deployment to Render / Railway.
  - Prepare a crisp 3-minute hackathon/pitch demo narrative following the team lead's pitch script.

---

## 7. Approval & Permission Gate

> **No code has been altered yet.**  
> Please review this plan. Once you confirm and approve, we will begin Phase 1: refining the database models and backend endpoints to match the PHC workflows.

