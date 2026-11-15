# 🏆 WardVault PHC: 3-Minute Pitch & Live Demo Script

**Competition:** Universal Service Provision Fund (USPF) Changemaker Challenge  
**Team:** The Alpha Hunters (Emmanuel Ikeh, Joseph, Glory)  
**Live Target:** Web / Offline Tablet Demo

---

## ⏱️ Minute 1: The Problem & The Paper Reality (60 seconds)

### What to Say:
> *"Good day, esteemed judges. In Nigeria, the 2026 Tech Outlook Report published by NITDA and the National Bureau of Statistics surveyed over 500 Primary Healthcare Centres. The findings were staggering:*
> - *Only **16.2%** of PHCs have working internet.*
> - *Over **38%** have unstable or zero electricity.*
> - *And over **73%** still rely entirely on physical paper folders.*
>
> *Most digital health startups build heavy cloud hospital software designed for private facilities in Victoria Island or Maitama. When taken to an underserved PHC in Alakia or rural Oyo State, they fail immediately because there is no connectivity, no power, and staff cannot migrate thousands of paper folders.*
>
> *Introducing **WardVault**: The offline-first patient records and care-coordination platform built specifically for Primary Healthcare Centres."*

---

## ⏱️ Minute 2: The Live Demonstration (60 seconds)

### Actions to Perform on Screen:
1. **Open the Login Screen:**
   - Click the quick button for **Amina Bello (CHEW)** (`PHC/26/CHEW/102`).
   - Click **Sign In to PHC Station**.
   - *Say:* *"Notice how our interface is designed for Community Health Extension Workers (CHEWs) and nurses, not complex hospital bureaucracy."*

2. **Open Patient Chart & Record Triage Vitals:**
   - In the **Active Patient Directory**, click on **Zainab Aliyu** (`ANC-042`).
   - Show the triage panel:
     - Enter Blood Pressure: `118/76`
     - Temperature: `37.2°C`
     - Malaria mRDT: Select `Positive (P. falciparum)`
     - Clinical Assessment: *"Patient in 2nd trimester presenting with fever. Started on artemether-lumefantrine."*
   - Click **Save Clinical Encounter**.
   - *Say:* *"In 10 seconds, Amina records vital signs, rapid malaria diagnostic test results, and prescriptions. Notice the live cryptographic audit hash computed at the bottom of the chart."*

3. **Demonstrate Paper Migration with Clinical Safety:**
   - Click the **Paper-to-Digital Intake** tab.
   - Show the physical folder input (`FL-4091`).
   - Point to the **⚠️ Flag Folder for Clinical Review** toggle:
   - *Say:* *"Here is our core differentiator: Paper-to-Digital transition. In real PHCs, handwriting on old folders is smudged or illegible. Under WardVault policy, data clerks never invent or guess missing dosages. They check this box, which pauses the record in a high-priority review queue until Nurse Folake physically verifies the paper chart."*

4. **Demonstrate Secondary Care Coordination (The Referral Tracker):**
   - Click the **Referral & Follow-Up Tracker** tab.
   - Show the active outbound referrals to **University College Hospital (UCH) Ibadan**.
   - Click **Mark Attended $\rightarrow$ Log Feedback $\rightarrow$ Complete Care**.
   - *Say:* *"PHCs cannot handle surgical or critical emergencies. WardVault coordinates referrals to regional tertiary hospitals like UCH and tracks the patient until care is completed, closing the primary-secondary care loop."*

---

## ⏱️ Minute 3: The Secret Weapon — Offline Resilience & Compliance (60 seconds)

### Actions to Perform on Screen:
1. **Simulate Network Failure:**
   - In the bottom-right resilience widget, click **Wi-Fi ON $\rightarrow$ toggle to Wi-Fi OFF**.
   - Notice the top alert turns amber: *"OFFLINE LOCAL MODE ACTIVE"*.
   - *Say:* *"Now, internet connectivity cuts out entirely. The staff doesn't stop working. Every consultation, vitals entry, and referral is queued into local encrypted IndexedDB storage."*

2. **Demonstrate Power Loss Alarm:**
   - Unplug the laptop power cord (or trigger the battery simulation).
   - The system triggers an instant audio tone and displays the battery warning.
   - *Say:* *"With over 38% of PHCs experiencing power blackouts, WardVault actively monitors hardware battery levels and alerts the nurse to switch to solar backup before the device shuts down."*

3. **Demonstrate Auto-Sync & Cryptographic Integrity:**
   - Click **Wi-Fi OFF $\rightarrow$ toggle back to Wi-Fi ON** (or click **Sync Now**).
   - The banner flashes green: *"Facility Records Synced & Cryptographically Verified"*.
   - Click **CPO Audit & SIEM** in the top navigation bar.
   - Click **🔍 Scan Ledger Integrity**.
   - The screen shows: **✅ Ledger Cryptographically Verified (0 Tampering Incidents)**.
   - *Say:* *"Every offline record automatically syncs back to the central gateway and is chained with SHA-256 cryptographic hashes. If an insider maliciously alters a clinical record in the database, the hash chain breaks instantly, guaranteeing complete compliance with the Nigeria Data Protection Act (NDPA) 2023."*

---

## 🎯 The Winning Closing Statement (15 seconds)

> *"WardVault does not ask Nigerian PHCs to wait for 100% broadband coverage or 24/7 power that may not arrive for years. We meet healthcare workers exactly where they are today: with offline-first software, structured paper migration, care coordination to secondary hospitals, and tamper-evident trust.*
>
> *Thank you, and we welcome your questions."*
