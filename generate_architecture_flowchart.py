import os
import math
from PIL import Image, ImageDraw, ImageFont

def create_technical_flowchart():
    # 3200 x 2200 Ultra-HD Presentation Resolution
    W, H = 3200, 2200
    img = Image.new("RGB", (W, H), color="#090D16") # Deep Engineering Dark Navy
    draw = ImageDraw.Draw(img)

    # Fonts
    font_bold = "C:/Windows/Fonts/segoeuib.ttf"
    font_reg = "C:/Windows/Fonts/segoeui.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:/Windows/Fonts/arialbd.ttf"
        font_reg = "C:/Windows/Fonts/arial.ttf"

    title_font = ImageFont.truetype(font_bold, 46)
    sub_font = ImageFont.truetype(font_reg, 22)
    node_hdr_font = ImageFont.truetype(font_bold, 20)
    node_body_font = ImageFont.truetype(font_reg, 16)
    node_code_font = ImageFont.truetype(font_bold, 15)
    decision_hdr_font = ImageFont.truetype(font_bold, 18)
    decision_sub_font = ImageFont.truetype(font_reg, 14)
    label_font = ImageFont.truetype(font_bold, 16)
    legend_font = ImageFont.truetype(font_bold, 17)

    # ------------------ TOP BANNER ------------------
    draw.rectangle([0, 0, W, 130], fill="#0F172A")
    draw.line([0, 130, W, 130], fill="#1E293B", width=3)
    draw.text((60, 22), "WARDVAULT PHC GATEWAY: TECHNICAL ARCHITECTURE & LOGIC FLOWCHART", fill="#FFFFFF", font=title_font)
    draw.text((60, 80), "Pre-Implementation System Design & Architectural Decision Hierarchy (Frontend, Offline Engine, Routing, Storage & Audit)", fill="#94A3B8", font=sub_font)

    # Legend on top right
    legend_items = [
        ("Terminal / Start-End", "#059669", "pill"),
        ("Decision Gate", "#D97706", "diamond"),
        ("Process / Subsystem", "#2563EB", "rect"),
        ("Storage / Ledger", "#DB2777", "rect")
    ]
    lx = W - 780
    for text, color, shape in legend_items:
        if shape == "pill":
            draw.rounded_rectangle([lx, 45, lx + 28, 75], radius=14, fill=color)
        elif shape == "diamond":
            draw.polygon([(lx + 14, 45), (lx + 28, 60), (lx + 14, 75), (lx, 60)], fill=color)
        else:
            draw.rounded_rectangle([lx, 47, lx + 28, 73], radius=6, fill=color)
        draw.text((lx + 36, 50), text, fill="#CBD5E1", font=legend_font)
        lx += 190

    # ------------------ DRAWING PRIMITIVES ------------------
    def draw_process(x, y, w, h, title, subtitle, tech=None, fill="#1E293B", outline="#3B82F6"):
        # Draw rounded rectangle
        draw.rounded_rectangle([x - w/2, y - h/2, x + w/2, y + h/2], radius=12, fill=fill, outline=outline, width=2)
        # Title
        bbox = node_hdr_font.getbbox(title)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw/2, y - h/2 + 14), title, fill="#FFFFFF", font=node_hdr_font)
        # Subtitle
        if subtitle:
            bbox_s = node_body_font.getbbox(subtitle)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((x - sw/2, y - h/2 + 42), subtitle, fill="#94A3B8", font=node_body_font)
        # Tech badge
        if tech:
            bbox_t = node_code_font.getbbox(tech)
            cw = bbox_t[2] - bbox_t[0]
            draw.text((x - cw/2, y + h/2 - 28), tech, fill=outline, font=node_code_font)

    def draw_terminal(x, y, w, h, text, sub=None, fill="#065F46", outline="#10B981"):
        draw.rounded_rectangle([x - w/2, y - h/2, x + w/2, y + h/2], radius=h/2, fill=fill, outline=outline, width=3)
        bbox = node_hdr_font.getbbox(text)
        tw = bbox[2] - bbox[0]
        ty = y - 18 if sub else y - 10
        draw.text((x - tw/2, ty), text, fill="#FFFFFF", font=node_hdr_font)
        if sub:
            bbox_s = node_body_font.getbbox(sub)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((x - sw/2, y + 6), sub, fill="#A7F3D0", font=node_body_font)

    def draw_decision(cx, cy, w, h, title, subtitle=None, fill="#78350F", outline="#F59E0B"):
        # Diamond shape
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
        ty = cy - 16 if subtitle else cy - 9
        draw.text((cx - tw/2, ty), title, fill="#FEF3C7", font=decision_hdr_font)
        if subtitle:
            bbox_s = decision_sub_font.getbbox(subtitle)
            sw = bbox_s[2] - bbox_s[0]
            draw.text((cx - sw/2, cy + 5), subtitle, fill="#FCD34D", font=decision_sub_font)

    def draw_flow_arrow(points, color="#94A3B8", label=None, label_offset=(-25, -20)):
        # Draw polyline
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color, width=3)
        # Arrowhead at last point
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 12
        draw.polygon([
            (x2, y2),
            (x2 - arrow_len * math.cos(angle - 0.45), y2 - arrow_len * math.sin(angle - 0.45)),
            (x2 - arrow_len * math.cos(angle + 0.45), y2 - arrow_len * math.sin(angle + 0.45))
        ], fill=color)
        if label:
            lx, ly = points[0]
            if len(points) > 2:
                lx, ly = points[1]
            draw.text((lx + label_offset[0], ly + label_offset[1]), label, fill=color, font=label_font)

    # ==================== FLOWCHART NODES & COORDINATES ====================
    # Center axis X = 1600. Let's arrange a logical top-to-bottom master flowchart with branches!

    # 1. START TERMINAL
    draw_terminal(1600, 190, 480, 64, "START: CLINICIAN LOGIN", "Primary Healthcare Centre Workstation", fill="#065F46", outline="#10B981")

    # 2. DECISION 1: Is Clinician On Duty?
    draw_flow_arrow([(1600, 222), (1600, 280)], color="#64748B")
    draw_decision(1600, 335, 360, 110, "Is Clinician On Duty?", "Verify Roster & Shift Status")

    # Branch: Not On Duty -> Read Only Session
    draw_flow_arrow([(1780, 335), (2050, 335), (2050, 420)], color="#EF4444", label="[NO: Off-Duty]", label_offset=(20, -22))
    draw_process(2050, 470, 380, 95, "Restricted Read-Only Access", "Block Consultations & Transfers", tech="403 Forbidden on Mutations", fill="#450A0A", outline="#EF4444")
    draw_flow_arrow([(2050, 518), (2050, 560), (1600, 560)], color="#EF4444")

    # Branch: On Duty -> Yes
    draw_flow_arrow([(1600, 390), (1600, 450)], color="#10B981", label="[YES: Authorized]", label_offset=(15, 10))

    # 3. PROCESS: Patient Intake & Census Search
    draw_process(1600, 500, 460, 100, "Patient Intake & Folder Retrieval", "Search by Name, Hospital No, Phone or NIN", tech="Client IndexedDB Fast Cache (<5ms)", fill="#1E293B", outline="#3B82F6")

    # 4. DECISION 2: Registered Patient?
    draw_flow_arrow([(1600, 550), (1600, 610)], color="#64748B")
    draw_decision(1600, 665, 380, 110, "Patient Registered in PHC?", "Check Local Physical & Digital Index")

    # Branch: New / Paper Migration (Left)
    draw_flow_arrow([(1410, 665), (1000, 665), (1000, 740)], color="#38BDF8", label="[NO: New Walk-in / Paper Card]", label_offset=(-220, -22))
    draw_process(1000, 800, 440, 115, "Staged Dual-Track Intake", "Digitize Card & Log Rack/Shelf Location", tech="Assign Primary 'HOSP-2026-XXX'", fill="#1E293B", outline="#38BDF8")
    draw_flow_arrow([(1000, 858), (1000, 930), (1380, 930)], color="#38BDF8")

    # Branch: Yes (Returning Patient)
    draw_flow_arrow([(1600, 720), (1600, 780)], color="#10B981", label="[YES: Returning]", label_offset=(15, 10))
    draw_process(1600, 830, 420, 100, "Load Patient Medical Folder", "Pull Longitudinal Vitals Trend & History", tech="Previous BP, Diagnoses & Medications", fill="#1E293B", outline="#10B981")
    draw_flow_arrow([(1600, 880), (1600, 930)], color="#64748B")

    # Merge into Offline/Online Network Decision
    draw_flow_arrow([(1380, 930), (1600, 930)], color="#64748B")

    # 5. DECISION 3: Is Network Online?
    draw_decision(1600, 985, 380, 110, "Is Network / LAN Available?", "Local Wi-Fi or Offline Workstation")

    # Branch: Offline (Left)
    draw_flow_arrow([(1410, 985), (650, 985), (650, 1050)], color="#F59E0B", label="[OFFLINE: Power Grid / ISP Down]", label_offset=(-230, -22))
    draw_process(650, 1110, 440, 115, "Local Storage Vault (IndexedDB)", "Buffer Encounters & Referrals in Browser", tech="ObjectStores: 'pending_encounters', 'referrals'", fill="#312E81", outline="#818CF8")

    # Branch: Online (Right / Direct)
    draw_flow_arrow([(1790, 985), (1950, 985), (1950, 1050)], color="#10B981", label="[ONLINE / LOCALHOST: Active Gateway]", label_offset=(15, -22))
    draw_process(1950, 1110, 440, 115, "FastAPI Local Server Gateway", "Async REST Endpoints & JWT Security", tech="uvicorn main:app --host 127.0.0.1:8000", fill="#1E293B", outline="#10B981")

    # Join offline buffer auto-sync
    draw_flow_arrow([(650, 1168), (650, 1220), (1600, 1220)], color="#818CF8", label="Background Sync Queue (/api/sync/batch)", label_offset=(20, -18))
    draw_flow_arrow([(1950, 1168), (1950, 1220), (1600, 1220)], color="#10B981")

    # 6. CENTRAL PROCESS: 6-Step Clinical Clerkship
    draw_flow_arrow([(1600, 1220), (1600, 1280)], color="#64748B")
    draw_process(1600, 1345, 680, 130, "6-Step Clinical Consultation Clerkship", "1. History & Chief Complaint  •  2. Vitals Triage (BP, Temp, Pulse, Glucose)\n3. Point-of-Care Lab (mRDT, PCV)  •  4. Diagnosis (Primary/Diff)\n5. Prescription & Pharmacy  •  6. Outcome Routing Decision", tech="Standard Nigerian MOH Primary Healthcare Protocols", fill="#1E293B", outline="#10B981")

    # 7. MASTER DECISION 4: Clinical Outcome Route Decision?
    draw_flow_arrow([(1600, 1410), (1600, 1475)], color="#64748B")
    draw_decision(1600, 1530, 480, 110, "Select Clinical Outcome Route?", "Determines Patient Care Destination")

    # ------------------- 4 CARE PATHWAYS BRANCHING -------------------
    # Path 1: Outpatient (Far Left, X = 450)
    # Path 2: Observation Ward (Mid Left, X = 1180)
    # Path 3: Secondary Referral (Mid Right, X = 2020)
    # Path 4: Follow-up & Outreach (Far Right, X = 2750)

    # Path 1: Outpatient
    draw_flow_arrow([(1360, 1530), (450, 1530), (450, 1610)], color="#38BDF8", label="[Route 1: Drugs & Home]", label_offset=(-180, -20))
    draw_process(450, 1675, 420, 125, "Outpatient Treatment Complete", "Dispense Pharmacy Medications & Advise", tech="Immediate Discharge to Home", fill="#1E293B", outline="#38BDF8")

    # Path 2: Observation Ward
    draw_flow_arrow([(1450, 1565), (1180, 1610)], color="#10B981", label="[Route 2: Admit Inpatient]", label_offset=(-180, 0))
    draw_process(1180, 1675, 430, 125, "Short-Stay Observation Ward", "Assign Observation Bed (Beds 01–03)", tech="Append Daily Ward Progress Notes", fill="#1E293B", outline="#10B981")

    # Path 3: Secondary Hospital Transfer
    draw_flow_arrow([(1750, 1565), (2020, 1610)], color="#F59E0B", label="[Route 3: Transfer]", label_offset=(15, 0))
    draw_process(2020, 1675, 460, 125, "Secondary Referral & Transfer", "Select Nearest Hospital (UCH / Adeoyo / Ring Rd)", tech="Auto-Generate 1-Page Official MOH Transfer Note", fill="#1E293B", outline="#F59E0B")

    # Transfer Handover reporting step below Path 3
    draw_flow_arrow([(2020, 1738), (2020, 1780)], color="#F59E0B")
    draw_process(2020, 1835, 460, 105, "Closed-Loop Handover Report", "Receiving Doctor, Ward & Arrival Vitals", tech="Counter-Referral Summary Back to PHC", fill="#1E293B", outline="#F59E0B")

    # Path 4: Follow-up & Appointment Outreach (Far Right)
    draw_flow_arrow([(1840, 1530), (2750, 1530), (2750, 1585)], color="#EC4899", label="[Route 4: Book Follow-Up]", label_offset=(20, -20))
    draw_process(2750, 1635, 450, 95, "Appointment Scheduled", "ANC, Hypertension, Diabetes, Immunization", tech="Logged with Patient Contact Phone", fill="#1E293B", outline="#EC4899")

    # Follow-up sub-decision: Is Doctor On Seat?
    draw_flow_arrow([(2750, 1683), (2750, 1720)], color="#EC4899")
    draw_decision(2750, 1770, 380, 95, "Is Doctor On Seat Today?", "Dr. Kemi Sanni Availability Status", fill="#831843", outline="#F43F5E")

    # Doctor Away Sub-Branches
    draw_flow_arrow([(2560, 1770), (2430, 1770), (2430, 1870)], color="#F43F5E", label="[NO: Away]", label_offset=(-90, -18))
    draw_process(2430, 1930, 390, 115, "Doctor-Away Contingency Call", "4 Pathways: Nurse Step-Down Refill, Reschedule,\nEmergency Tele-Consult, or Secondary Transfer", tech="Structured Clinic Protocol Handled via Phone", fill="#4C0519", outline="#F43F5E")

    draw_flow_arrow([(2750, 1818), (2750, 1870)], color="#10B981", label="[YES: In Clinic]", label_offset=(10, 10))
    draw_process(2750, 1930, 380, 115, "Routine Appointment Outreach", "Click-to-Dial Phone Reminder (080...)", tech="Status: 'Appointment Confirmed'", fill="#1E293B", outline="#10B981")

    # ------------------- STORAGE & AUDIT TIER (BOTTOM CONVERGENCE) -------------------
    # Converge all care pathways to SQLite persistence
    bottom_y = 2050
    draw.line([(450, 1738), (450, bottom_y - 30), (1600, bottom_y - 30)], fill="#3B82F6", width=3)
    draw.line([(1180, 1738), (1180, bottom_y - 30)], fill="#10B981", width=3)
    draw.line([(2020, 1888), (2020, bottom_y - 30), (1600, bottom_y - 30)], fill="#F59E0B", width=3)
    draw.line([(2430, 1988), (2430, bottom_y - 30)], fill="#F43F5E", width=3)
    draw.line([(2750, 1988), (2750, bottom_y - 30), (1600, bottom_y - 30)], fill="#10B981", width=3)

    draw_flow_arrow([(1600, bottom_y - 30), (1600, bottom_y)], color="#64748B")

    # Bottom Two Master Engines: Clinical DB + Cryptographic Audit
    # Left Box: Clinical DB
    draw_process(1200, bottom_y + 40, 680, 85, "Local ACID Clinical Database (wardvault_clinical.db)", "Atomic Tables: patients, clinical_encounters, short_stay_admissions, referrals, followup_calls", tech="SQLite Zero-Cloud Engine with Asyncpg Connection Wrapper", fill="#1E293B", outline="#3B82F6")

    # Arrow from Clinical to Audit
    draw_flow_arrow([(1540, bottom_y + 40), (1660, bottom_y + 40)], color="#DB2777", label="Hash Chain", label_offset=(-40, -20))

    # Right Box: Audit Ledger
    draw_process(2020, bottom_y + 40, 680, 85, "Cryptographic Audit Ledger (wardvault_audit.db)", "Immutable SHA-256 Block Chaining: H(user | action | target_patient | reason | prev_hash)", tech="NDPA 2023 Verified Compliance • Tamper-Evident Ledger Integrity", fill="#1E293B", outline="#DB2777")

    # Final Terminals
    draw_terminal(2880, bottom_y + 40, 380, 60, "VERIFIED SECURE", "100% Offline Primary Care Record", fill="#065F46", outline="#10B981")
    draw_flow_arrow([(2360, bottom_y + 40), (2690, bottom_y + 40)], color="#10B981")

    # Save PNG files
    out_path = os.path.abspath("wardvault_flowchart_architecture.png")
    img.save(out_path, format="PNG", dpi=(300, 300))
    print(f"✅ Generated authentic technical architecture flowchart: {out_path} ({W}x{H} px)")

    # Copy to artifact directory
    artifact_dir = r"C:\Users\LENOVO PC\.gemini\antigravity\brain\43987be2-af25-4fc4-9217-ce21f4eafe9b"
    if os.path.exists(artifact_dir):
        artifact_path = os.path.join(artifact_dir, "wardvault_flowchart_architecture.png")
        img.save(artifact_path, format="PNG", dpi=(300, 300))
        print(f"✅ Copied to artifact dir: {artifact_path}")

    return out_path

if __name__ == "__main__":
    create_technical_flowchart()
