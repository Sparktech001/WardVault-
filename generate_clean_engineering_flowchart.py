import os
import math
from PIL import Image, ImageDraw, ImageFont

def build_engineering_flowchart():
    # 3200 x 2400 High-Resolution Professional Engineering Blueprint (Clean Monochrome / Minimalist Slate)
    W, H = 3200, 2400
    img = Image.new("RGB", (W, H), color="#FFFFFF") # Clean White Background
    draw = ImageDraw.Draw(img)

    # Fonts
    font_bold = "C:/Windows/Fonts/segoeuib.ttf"
    font_reg = "C:/Windows/Fonts/segoeui.ttf"
    font_mono = "C:/Windows/Fonts/consola.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:/Windows/Fonts/arialbd.ttf"
        font_reg = "C:/Windows/Fonts/arial.ttf"
        font_mono = "C:/Windows/Fonts/cour.ttf"

    title_font = ImageFont.truetype(font_bold, 42)
    sub_font = ImageFont.truetype(font_reg, 20)
    boundary_font = ImageFont.truetype(font_bold, 18)
    node_hdr_font = ImageFont.truetype(font_bold, 18)
    node_body_font = ImageFont.truetype(font_reg, 15)
    node_code_font = ImageFont.truetype(font_bold, 13)
    decision_hdr_font = ImageFont.truetype(font_bold, 16)
    decision_sub_font = ImageFont.truetype(font_reg, 13)
    label_font = ImageFont.truetype(font_bold, 14)
    legend_font = ImageFont.truetype(font_bold, 15)

    # ------------------ TOP TECHNICAL HEADER ------------------
    draw.line([60, 40, W - 60, 40], fill="#0F172A", width=4)
    draw.text((60, 52), "WARDVAULT PHC GATEWAY — TECHNICAL ARCHITECTURE & SYSTEM DESIGN FLOWCHART", fill="#0F172A", font=title_font)
    draw.text((60, 106), "Pre-Implementation Architectural Specification: Offline-First Reliability, Clinical Clerkship, Decision Logic & Audit Verification", fill="#475569", font=sub_font)
    draw.line([60, 145, W - 60, 145], fill="#CBD5E1", width=2)

    # Clean Monochrome Legend
    legend = [
        ("Terminal / State", "pill"),
        ("Decision Gate", "diamond"),
        ("System Process", "rect"),
        ("Data Store / Ledger", "cylinder")
    ]
    lx = W - 780
    for text, shape in legend:
        if shape == "pill":
            draw.rounded_rectangle([lx, 70, lx + 26, 96], radius=13, fill="#F1F5F9", outline="#0F172A", width=2)
        elif shape == "diamond":
            draw.polygon([(lx + 13, 70), (lx + 26, 83), (lx + 13, 96), (lx, 83)], fill="#F8FAFC", outline="#0F172A")
        elif shape == "cylinder":
            draw.rectangle([lx, 72, lx + 26, 94], fill="#F1F5F9", outline="#0F172A", width=2)
            draw.line([lx, 78, lx + 26, 78], fill="#0F172A", width=1)
        else:
            draw.rectangle([lx, 72, lx + 26, 94], fill="#F8FAFC", outline="#0F172A", width=2)
        draw.text((lx + 34, 75), text, fill="#334155", font=legend_font)
        lx += 180

    # ------------------ DRAWING HELPERS ------------------
    def draw_process(x, y, w, h, title, subtitle=None, tech=None, fill="#FFFFFF", outline="#0F172A"):
        # Rounded process box
        draw.rounded_rectangle([x - w/2, y - h/2, x + w/2, y + h/2], radius=8, fill=fill, outline=outline, width=2)
        bbox = node_hdr_font.getbbox(title)
        tw = bbox[2] - bbox[0]
        ty = y - h/2 + 12
        draw.text((x - tw/2, ty), title, fill="#0F172A", font=node_hdr_font)
        
        if subtitle:
            for i, line in enumerate(subtitle.split("\n")):
                bbox_s = node_body_font.getbbox(line)
                sw = bbox_s[2] - bbox_s[0]
                draw.text((x - sw/2, ty + 26 + (i * 20)), line, fill="#475569", font=node_body_font)

        if tech:
            bbox_t = node_code_font.getbbox(tech)
            cw = bbox_t[2] - bbox_t[0]
            draw.text((x - cw/2, y + h/2 - 24), tech, fill="#0F172A", font=node_code_font)

    def draw_terminal(x, y, w, h, text, sub=None, fill="#F8FAFC", outline="#0F172A"):
        draw.rounded_rectangle([x - w/2, y - h/2, x + w/2, y + h/2], radius=h/2, fill=fill, outline=outline, width=3)
        bbox = node_hdr_font.getbbox(text)
        tw = bbox[2] - bbox[0]
        ty = y - 16 if sub else y - 10
        draw.text((x - tw/2, ty), text, fill="#0F172A", font=node_hdr_font)
        if sub:
            bbox_s = node_body_font.getbbox(sub)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((x - sw/2, y + 6), sub, fill="#475569", font=node_body_font)

    def draw_decision(cx, cy, w, h, title, subtitle=None, fill="#F8FAFC", outline="#0F172A"):
        pts = [
            (cx, cy - h/2),
            (cx + w/2, cy),
            (cx, cy + h/2),
            (cx - w/2, cy)
        ]
        draw.polygon(pts, fill=fill, outline=outline)
        draw.line(pts + [pts[0]], fill=outline, width=2)
        bbox = decision_hdr_font.getbbox(title)
        tw = bbox[2] - bbox[0]
        ty = cy - 15 if subtitle else cy - 8
        draw.text((cx - tw/2, ty), title, fill="#0F172A", font=decision_hdr_font)
        if subtitle:
            bbox_s = decision_sub_font.getbbox(subtitle)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((cx - sw/2, cy + 4), subtitle, fill="#64748B", font=decision_sub_font)

    def draw_data_store(x, y, w, h, title, subtitle=None, tech=None):
        # Database cylinder symbol
        draw.rounded_rectangle([x - w/2, y - h/2, x + w/2, y + h/2], radius=6, fill="#F8FAFC", outline="#0F172A", width=2)
        draw.line([x - w/2, y - h/2 + 10, x + w/2, y - h/2 + 10], fill="#0F172A", width=2)
        bbox = node_hdr_font.getbbox(title)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw/2, y - h/2 + 16), title, fill="#0F172A", font=node_hdr_font)
        if subtitle:
            bbox_s = node_body_font.getbbox(subtitle)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((x - sw/2, y - h/2 + 42), subtitle, fill="#475569", font=node_body_font)
        if tech:
            bbox_t = node_code_font.getbbox(tech)
            cw = bbox_t[2] - bbox_t[0]
            draw.text((x - cw/2, y + h/2 - 24), tech, fill="#0F172A", font=node_code_font)

    def draw_arrow(points, label=None, label_offset=(10, -18)):
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill="#0F172A", width=2)
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 11
        draw.polygon([
            (x2, y2),
            (x2 - arrow_len * math.cos(angle - 0.4), y2 - arrow_len * math.sin(angle - 0.4)),
            (x2 - arrow_len * math.cos(angle + 0.4), y2 - arrow_len * math.sin(angle + 0.4))
        ], fill="#0F172A")
        if label:
            lx, ly = points[0]
            if len(points) > 2:
                lx, ly = points[1]
            draw.text((lx + label_offset[0], ly + label_offset[1]), label, fill="#0F172A", font=label_font)

    # ------------------ ARCHITECTURAL SYSTEM BOUNDARIES ------------------
    # Boundary 1: Client Layer (Left/Center Top)
    draw.rounded_rectangle([80, 165, 3120, 1260], radius=16, fill="#FBFCFD", outline="#94A3B8", width=1)
    draw.text((105, 175), "BOUNDARY 1: CLINICAL CLIENT TIER (OFFLINE-FIRST PHC WORKSTATION — HTML5 / TAILWINDCSS / ALPINE.JS)", fill="#475569", font=boundary_font)

    # Boundary 2: Decision Routing & Care Execution
    draw.rounded_rectangle([80, 1285, 3120, 1970], radius=16, fill="#FFFFFF", outline="#94A3B8", width=1)
    draw.text((105, 1295), "BOUNDARY 2: CLINICAL CARE EXECUTION & MULTI-PATHWAY ROUTING (OUTPATIENT, WARD, REFERRAL, OUTREACH)", fill="#475569", font=boundary_font)

    # Boundary 3: Gateway & Cryptographic Persistence
    draw.rounded_rectangle([80, 1995, 3120, 2340], radius=16, fill="#F8FAFC", outline="#94A3B8", width=1)
    draw.text((105, 2005), "BOUNDARY 3: LOCAL GATEWAY & IMMUTABLE PERSISTENCE TIER (FASTAPI ASYNC ENGINE + DUAL SQLITE LEDGERS)", fill="#475569", font=boundary_font)

    # ==================== SECTION 1: INTAKE & AUTHENTICATION ====================
    # Start Node
    draw_terminal(1600, 230, 480, 60, "START: CLINICIAN ACCESS", "Alakia PHC Workstation Initialized")

    # Decision 1: Shift Verification
    draw_arrow([(1600, 260), (1600, 310)])
    draw_decision(1600, 365, 360, 105, "Is Clinician On Duty?", "Verify Staff Roster & Cadre")

    # Off-Duty -> Deny / Read Only
    draw_arrow([(1780, 365), (2180, 365), (2180, 435)], label="[No: Off-Duty]", label_offset=(20, -18))
    draw_process(2180, 485, 380, 95, "Restricted Read-Only Session", "Clinical write actions disabled", tech="HTTP 403 Forbidden on writes", fill="#F1F5F9")
    draw_arrow([(2180, 535), (2180, 595), (1600, 595)])

    # On-Duty -> Proceed
    draw_arrow([(1600, 418), (1600, 485)], label="[Yes: Authorized]", label_offset=(12, 10))

    # Patient Search / Intake
    draw_process(1600, 535, 460, 95, "Patient Intake & Records Lookup", "Query by Name, Hospital No, Phone, or NIN", tech="Client IndexedDB Fast Cache (<5ms)")

    # Decision 2: Registration Status
    draw_arrow([(1600, 585), (1600, 640)])
    draw_decision(1600, 695, 380, 105, "Patient Registered in PHC?", "Check Local Physical & Digital Index")

    # Branch: Unregistered / Paper Card (Left)
    draw_arrow([(1410, 695), (960, 695), (960, 765)], label="[No: New Walk-In / Paper Card]", label_offset=(-220, -18))
    draw_process(960, 825, 460, 115, "Staged Dual-Track Paper Intake", "Digitize card details; retain paper folder as legal proof\nLog physical Records Room location (Rack/Shelf)", tech="Generate Primary 'HOSP-2026-XXX'")
    draw_arrow([(960, 885), (960, 945), (1380, 945)])

    # Branch: Registered / Returning Patient (Down)
    draw_arrow([(1600, 750), (1600, 815)], label="[Yes: Existing Folder]", label_offset=(12, 10))
    draw_process(1600, 865, 440, 95, "Load Longitudinal Patient Folder", "Retrieve past visits, vitals history & diagnoses", tech="Full Medical History Chain Available")
    draw_arrow([(1600, 915), (1600, 945)])

    # Merge into Network Availability Gate
    draw_arrow([(1380, 945), (1600, 945)])

    # Decision 3: Network / Local Gateway Status
    draw_arrow([(1600, 945), (1600, 995)])
    draw_decision(1600, 1050, 400, 105, "Is Local Gateway Reachable?", "Check LAN Wi-Fi / Localhost Daemon")

    # Offline Branch (Left)
    draw_arrow([(1400, 1050), (600, 1050), (600, 1115)], label="[Offline: Grid / Power Failure]", label_offset=(-230, -18))
    draw_process(600, 1175, 440, 110, "Local Storage Vault (IndexedDB)", "Buffer encounters and referrals inside browser\nAuto-reconciles when connection returns", tech="ObjectStores: pending_encounters, referrals", fill="#F1F5F9")
    draw_arrow([(600, 1230), (600, 1260), (1500, 1260)])

    # Online / Localhost Branch (Right)
    draw_arrow([(1800, 1050), (2000, 1050), (2000, 1115)], label="[Online: Active Gateway]", label_offset=(15, -18))
    draw_process(2000, 1175, 440, 110, "FastAPI Local Services Gateway", "Direct asynchronous request dispatch\nRole-based JWT session authentication", tech="uvicorn main:app --host 127.0.0.1:8000")
    draw_arrow([(2000, 1230), (2000, 1260), (1700, 1260)])

    # ==================== SECTION 2: CLINICAL CONSULTATION ====================
    draw_arrow([(1600, 1260), (1600, 1335)])
    draw_process(1600, 1400, 740, 125, "Standardized 6-Step Clinical Consultation Clerkship", "Step 1: History of Presenting Illness  •  Step 2: Baseline Triage Vitals (BP, Temp, Pulse, Glucose)\nStep 3: Point-of-Care Tests (mRDT, PCV, Urine)  •  Step 4: Diagnosis (Primary & Differential)\nStep 5: Drug Prescription & Dispensing  •  Step 6: Care Outcome Destination Router", tech="Standard Nigerian Federal Ministry of Health PHC Clinical Protocol")

    # ==================== SECTION 3: CARE OUTCOME DECISION ====================
    draw_arrow([(1600, 1465), (1600, 1515)])
    draw_decision(1600, 1570, 520, 105, "Select Clinical Disposition Outcome?", "Determines Patient Care Pathway")

    # 4 Output Branches:
    # 1. Outpatient (X = 420)
    # 2. Short-Stay Inpatient Observation (X = 1140)
    # 3. Secondary Referral & Handover (X = 1960)
    # 4. Follow-Up & Doctor Availability (X = 2760)

    # Pathway 1: Outpatient
    draw_arrow([(1340, 1570), (420, 1570), (420, 1640)], label="[Route 1: Drugs & Home]", label_offset=(-180, -18))
    draw_process(420, 1705, 410, 120, "Outpatient Disposition", "Medication dispensed at PHC dispensary\nPatient counseled on adherence", tech="Routine Care Episode Closed")

    # Pathway 2: Observation Ward
    draw_arrow([(1440, 1605), (1140, 1640)], label="[Route 2: Admit Bed]", label_offset=(-150, 0))
    draw_process(1140, 1705, 430, 120, "Short-Stay Observation Ward", "Bed assigned (Observation Beds 01–03)\nDaily multidisciplinary ward progress notes", tech="1–3 Days Inpatient Stabilization")

    # Pathway 3: Secondary Transfer
    draw_arrow([(1760, 1605), (1960, 1640)], label="[Route 3: Transfer]", label_offset=(15, 0))
    draw_process(1960, 1705, 460, 120, "Secondary Hospital Transfer", "Select nearest hospital (UCH / Adeoyo / Ring Road)\nGenerate 1-Page Official MOH Transfer Note", tech="Auto-pulls baseline vitals & stabilization")

    draw_arrow([(1960, 1765), (1960, 1815)])
    draw_process(1960, 1870, 460, 105, "Closed-Loop Handover Report", "Record receiving doctor, receiving ward & arrival vitals\nCounter-referral feedback linked back to PHC", tech="Verified Complete Patient Transfer Chain")

    # Pathway 4: Follow-Up & Doctor Absence Coordination
    draw_arrow([(1860, 1570), (2760, 1570), (2760, 1630)], label="[Route 4: Schedule Follow-Up]", label_offset=(15, -18))
    draw_process(2760, 1675, 450, 85, "Appointment Scheduled", "Return date recorded for ANC, NCD or Immunization", tech="Logged with contact phone (080...)")

    # Sub-Decision: Doctor Availability
    draw_arrow([(2760, 1718), (2760, 1760)])
    draw_decision(2760, 1810, 390, 95, "Is Medical Officer On Seat?", "Dr. Kemi Sanni Duty Availability")

    # Doctor Away (Left sub-branch)
    draw_arrow([(2565, 1810), (2430, 1810), (2430, 1880)], label="[No: Away]", label_offset=(-80, -16))
    draw_process(2430, 1940, 400, 110, "Doctor-Away Contingency Call", "4 Structured Options: Nurse Step-Down Refill,\nReschedule via Call, Tele-Consult, or Urgent Transfer", tech="Active Clinic Coordination via Mobile Phone", fill="#F1F5F9")

    # Doctor Present (Down sub-branch)
    draw_arrow([(2760, 1858), (2760, 1885)], label="[Yes: In Clinic]", label_offset=(10, 8))
    draw_process(2760, 1940, 380, 105, "Routine Appointment Outreach", "Click-to-dial reminder call to patient (080...)\nRecord status: 'Appointment Confirmed'", tech="Pre-Appointment Attendance Guaranteed")

    # ==================== SECTION 4: STORAGE & IMMUTABLE AUDIT ====================
    conv_y = 2080
    # Converge all execution paths
    draw.line([(420, 1768), (420, conv_y), (1600, conv_y)], fill="#0F172A", width=2)
    draw.line([(1140, 1768), (1140, conv_y)], fill="#0F172A", width=2)
    draw.line([(1960, 1925), (1960, conv_y), (1600, conv_y)], fill="#0F172A", width=2)
    draw.line([(2430, 1995), (2430, conv_y)], fill="#0F172A", width=2)
    draw.line([(2760, 1995), (2760, conv_y), (1600, conv_y)], fill="#0F172A", width=2)

    draw_arrow([(1600, conv_y), (1600, 2125)])

    # Left: Clinical DB
    draw_data_store(1150, 2190, 680, 110, "Clinical Database (wardvault_clinical.db)", "Local SQLite Relational Schema: patients, encounters, admissions, referrals, followups", tech="Zero-Cloud Hardware Residency • Asyncpg Emulation Wrapper")

    # Arrow from Clinical to Audit
    draw_arrow([(1490, 2190), (1670, 2190)], label="SHA-256 Block", label_offset=(-45, -20))

    # Right: Audit Ledger
    draw_data_store(2030, 2190, 680, 110, "Cryptographic Audit Ledger (wardvault_audit.db)", "Immutable Hash Chain: H(user | action | patient_id | reason | prev_hash)", tech="Continuous Mathematical Ledger Verification • NDPA 2023 Compliant")

    # Final Terminal
    draw_arrow([(2370, 2190), (2660, 2190)])
    draw_terminal(2880, 2190, 410, 65, "TRANSACTION SECURED", "100% Offline Integrity Verified")

    # ------------------ FOOTER ------------------
    draw.line([60, H - 40, W - 60, H - 40], fill="#0F172A", width=2)
    draw.text((60, H - 32), "WardVault PHC Gateway Engineering Specification Blueprint • Federal Ministry of Health / USPF PHC Pilot Reference Architecture", fill="#64748B", font=node_code_font)
    draw.text((W - 580, H - 32), "System Architecture Flowchart • 100% Offline Capable • NDPA 2023 Compliant", fill="#64748B", font=node_code_font)

    # Save PNG
    out_path = os.path.abspath("wardvault_flowchart_architecture.png")
    img.save(out_path, format="PNG", dpi=(300, 300))
    print(f"✅ Generated clean engineering flowchart: {out_path} ({W}x{H} px)")

    # Copy to artifact dir
    artifact_dir = r"C:\Users\LENOVO PC\.gemini\antigravity\brain\43987be2-af25-4fc4-9217-ce21f4eafe9b"
    if os.path.exists(artifact_dir):
        artifact_path = os.path.join(artifact_dir, "wardvault_flowchart_architecture.png")
        img.save(artifact_path, format="PNG", dpi=(300, 300))
        print(f"✅ Copied clean flowchart to artifact dir: {artifact_path}")

    return out_path

if __name__ == "__main__":
    build_engineering_flowchart()
