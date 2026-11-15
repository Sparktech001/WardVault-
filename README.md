# WardVault PHC 🏥

**Offline-First Patient Records & Care-Coordination Platform for Underserved Primary Healthcare Centres (PHCs)**

Built for the **Universal Service Provision Fund (USPF) Changemaker Challenge**  
Developed by **The Alpha Hunters** (Emmanuel Ikeh, Joseph, Glory)

---

## 📌 Executive Overview

According to the **2026 Nigeria Tech Outlook Report** (published by NITDA in partnership with the National Bureau of Statistics across 539 Primary Healthcare Centres):
- **Only 16.2%** of PHCs have working internet access.
- **Only 37.8%** have working computers or tablets for records.
- **Only 26.4%** keep electronic or mixed patient records.
- **61.3%** have an intermittent power source (leaving 38.7% with no stable electricity).

**WardVault** directly solves this implementation gap. Rather than building another complex, cloud-dependent hospital EMR, WardVault is designed specifically around the daily realities of an individual Primary Healthcare Centre in Nigeria: **zero reliable internet, unstable power, stacks of legacy paper folders, and community health workers (CHEWs) managing frontline patient care.**

---

## ⚡ Core Capabilities

### 1. Offline-First Facility Architecture
- Operates 100% offline using a local laptop or mini-PC acting as the local server over a local area network (LAN) router.
- Tablets used by Community Health Extension Workers (CHEWs) and nurses run on an **Encrypted IndexedDB local queue**.
- When cellular or internet connectivity is detected, changes **automatically batch-sync** to the central health gateway without disrupting active consultations.
- **Hardware Power Detection:** Integrates with the device Battery API to emit audible alerts when AC mains power is cut, alerting clinical staff to switch to solar or inverter backup before data loss occurs.

### 2. Structured Paper-to-Digital Migration Workflow
- Many PHCs struggle to transition from physical paper folders to digital software.
- WardVault provides a dedicated **Paper Intake Mode** supporting legacy folder cards (`FL-1000`, `MED-118`), National Identity Numbers (**NIN**), and Basic Health Care Provision Fund (**BHCPF ID**).
- **Clinical Safety Safeguard:** Data-entry clerks can check *"Flag Folder for Clinical Review"* when handwriting is faded or ambiguous. This pauses clinical finalization in a dedicated review queue until Nurse In-Charge confirms the original physical chart.

### 3. Outpatient Care & Triage Vitals
- Built specifically for the most frequent PHC presentations in Nigeria:
  - **Triage Vitals:** Blood Pressure (mmHg), Temperature (°C), Pulse (bpm), Weight (kg).
  - **Malaria Rapid Diagnostic Testing (mRDT):** Tracking *Plasmodium falciparum* results.
  - **Maternal & Antenatal Care (ANC):** Trimester tracking and fetal checks.
  - **Routine Childhood Immunizations** and chronic disease screening (Hypertension & Diabetes).

### 4. Primary-to-Secondary Care Coordination (Referrals)
- Primary Healthcare Centres cannot handle advanced surgical or critical cases.
- WardVault features an **Outbound Referral Registry** linking the PHC to secondary facilities (e.g. University College Hospital (UCH), Adeoyo State Hospital, General Hospitals).
- Tracks the closed-loop patient lifecycle:  
  $$\text{Referred} \longrightarrow \text{Attended Secondary Facility} \longrightarrow \text{Clinical Feedback Received} \longrightarrow \text{Completed}$$

### 5. Cryptographic Audit Ledger (NDPA 2023 Compliance)
- Enforces the **Nigeria Data Protection Act (NDPA) 2023** for sensitive health data.
- Every consultation, paper transcription, and referral is SHA-256 hash-chained to the preceding block:
  $$\text{Current Hash} = \text{SHA-256}(\text{User ID} \mid \text{Action} \mid \text{Patient ID} \mid \text{Reason} \mid \text{Previous Hash})$$
- Tamper-evident: any unauthorized alteration at the database level breaks the cryptographic chain and triggers instant alarms in the Chief Privacy Officer (CPO) SIEM console (`/admin`).

---

## 🏗️ Architecture

```
[Local Primary Healthcare Centre]
  CHEW Tablet (Wi-Fi) -----\
  Nurse Laptop (LAN) -------> [ Local WardVault Gateway (FastAPI) ]
  Records Desk (LAN) ------/               |
                               [ Encrypted SQLite Database ]
                               [ Pending Sync Queue (IndexedDB) ]
                                           |
                                           v (Auto-Sync when cellular/Wi-Fi connects)
[Central Cloud Gateway (Render)]
  Remote Evaluators / USPF Judges ---> [ Live Web Gateway & SIEM Ledger ]
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Setup & Installation
```powershell
# Clone the repository
git clone https://github.com/Sparktech001/WardVault-.git
cd WardVault-

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install verified dependencies
pip install -r requirements.txt

# Seed the PHC database (278 staff, 114 patients)
python restore_dataset.py
```

### 3. Run the Application
```powershell
# Windows 1-Click Launcher:
.\run_wardvault.bat

# Or run via uvicorn directly:
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser:
- **Clinical Web Station:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **CPO SIEM & Audit Console:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 👥 Demo Clinical Accounts

| Staff Member | Role | Provider ID | Password | Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Amina Bello** | CHEW | `PHC/26/CHEW/102` | `password123` | Outpatient triage, vitals, malaria mRDT screening |
| **Folake Adeleke** | Nurse / Midwife | `PHC/26/NUR/103` | `password123` | Antenatal care & reviewing flagged paper folders |
| **Ibrahim Musa** | Records Officer | `PHC/26/REC/101` | `password123` | Paper folder transcription and patient indexing |
| **Dr. Raphael Thompson** | Facility In-Charge | `PHC/26/INC/104` | `password123` | Care coordination & outbound hospital referrals |
| **Vernita Cartwright** | CHEW (Off-Duty) | `PHC/26/CHEW/105` | `password123` | Demonstration of strict off-duty ABAC access locks |

---

## ☁️ Cloud Deployment (Render)

This repository includes [`render.yaml`](render.yaml) and [`Procfile`](Procfile) for zero-config deployment:

1. Connect this repo to [Render](https://render.com).
2. Create a **Web Service**.
3. Render automatically executes:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. No environment variables are required — database and cryptographic keys are fully self-contained.

---

## 📜 License & Compliance
Built by **The Alpha Hunters** for the **USPF Changemaker Challenge**.  
Compliant with the provisions of the **Nigeria Data Protection Act (NDPA) 2023**.
