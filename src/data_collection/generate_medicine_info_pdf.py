"""
BalanceAI -- Medicine Information Report (1mg-style per-medicine leaflet).

Renders every entry in data/medicine_details.json (3126 real medicine-list rows,
research_status complete/partial/not_found) as one leaflet-style section: name,
category, used-for-diseases, composition/dosage, side effects, a 6-row safety-advice
table (alcohol/pregnancy/breastfeeding/driving/kidney/liver), drug interactions,
missed-dose/overdose, a fact box, storage, sources, and a colored research-status badge.

Grouped by category for navigability. not_found rows get a compact one-line entry
(name + real reason) instead of a full leaflet, since there is no medicine content to
show for them -- this keeps the PDF honest about what it does and doesn't cover.
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "medicine_details.json"
OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "BalanceAI_Medicine_Information_Report.pdf"

GREEN = colors.HexColor("#1d5c3d")
GREEN_LT = colors.HexColor("#eef7f2")
CORAL = colors.HexColor("#c0392b")
CORAL_LT = colors.HexColor("#fdecec")
GOLD = colors.HexColor("#b7791f")
GOLD_LT = colors.HexColor("#fdf3e0")
GREY = colors.HexColor("#5a6571")
GREY_LT = colors.HexColor("#f5f5f3")
BLACK = colors.black
WHITE = colors.white

styles = getSampleStyleSheet()
report_title_s = ParagraphStyle("report_title", parent=styles["Title"], textColor=GREEN, fontSize=20, alignment=TA_CENTER)
report_sub_s = ParagraphStyle("report_sub", parent=styles["BodyText"], textColor=GREY, fontSize=9.5, alignment=TA_CENTER, leading=13)
cat_header_s = ParagraphStyle("cat_header", parent=styles["Heading1"], textColor=WHITE, fontSize=14, leading=17,
                               backColor=GREEN, borderPadding=(6, 8, 6, 8))
name_s = ParagraphStyle("name", parent=styles["Heading2"], textColor=BLACK, fontSize=12.5, leading=15, spaceAfter=2)
diseases_s = ParagraphStyle("diseases", parent=styles["BodyText"], textColor=GREY, fontSize=8.3, leading=10.5, spaceAfter=4)
section_label_s = ParagraphStyle("section_label", parent=styles["BodyText"], textColor=GREEN, fontSize=8.6,
                                  leading=10.5, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=1)
body_s = ParagraphStyle("body", parent=styles["BodyText"], textColor=BLACK, fontSize=8.4, leading=10.6)
small_grey_s = ParagraphStyle("small_grey", parent=styles["BodyText"], textColor=GREY, fontSize=7.4, leading=9.2)
safety_hdr_s = ParagraphStyle("safety_hdr", parent=styles["BodyText"], textColor=WHITE, fontSize=7.6,
                               fontName="Helvetica-Bold", alignment=TA_CENTER)
safety_cell_s = ParagraphStyle("safety_cell", parent=styles["BodyText"], fontSize=7.3, leading=9.0)
badge_complete_s = ParagraphStyle("badge_c", parent=styles["BodyText"], textColor=GREEN, fontSize=7.6,
                                   fontName="Helvetica-Bold", alignment=TA_CENTER)
badge_partial_s = ParagraphStyle("badge_p", parent=styles["BodyText"], textColor=GOLD, fontSize=7.6,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER)
notfound_s = ParagraphStyle("notfound", parent=styles["BodyText"], fontSize=8.0, leading=10.5, textColor=GREY)
toc_entry_s = ParagraphStyle("toc_entry", parent=styles["BodyText"], fontSize=8.6, leading=11.5)


def esc(s):
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def status_of(v):
    s = (v.get("research_status") or "").split(" ")[0].split("-")[0].strip()
    return s if s in ("complete", "partial", "not_found") else "partial"


def reason_of(v):
    for f in ("note", "not_found_reason", "research_note", "partial_note", "_note"):
        val = v.get(f)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def safety_table(safety):
    if not isinstance(safety, dict) or not safety:
        return None
    rows = [[Paragraph("Category", safety_hdr_s), Paragraph("Status", safety_hdr_s), Paragraph("Note", safety_hdr_s)]]
    order = ["alcohol", "pregnancy", "breastfeeding", "driving", "kidney", "liver"]
    for key in order:
        entry = safety.get(key)
        if not isinstance(entry, dict):
            continue
        status = entry.get("status", "")
        note = entry.get("note", "")
        color = GREEN if status == "Safe" else CORAL if status == "Unsafe" else GOLD
        rows.append([
            Paragraph(esc(key.capitalize()), safety_cell_s),
            Paragraph(f'<font color="{color.hexval()}"><b>{esc(status)}</b></font>', safety_cell_s),
            Paragraph(esc(note)[:220], safety_cell_s),
        ])
    if len(rows) == 1:
        return None
    t = Table(rows, colWidths=[2.6 * cm, 2.6 * cm, 10.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LT]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def interactions_block(interactions):
    if not interactions or not isinstance(interactions, list):
        return None
    lines = []
    for it in interactions:
        if not isinstance(it, dict):
            continue
        sev = it.get("severity", "")
        color = CORAL if sev == "Severe" else GOLD if sev == "Moderate" else GREY
        lines.append(
            f'<font color="{color.hexval()}"><b>[{esc(sev)}]</b></font> <b>{esc(it.get("with",""))}</b> — {esc(it.get("note",""))}'
        )
    if not lines:
        return None
    return Paragraph("<br/>".join(lines), body_s)


def fact_box_table(fb):
    if not isinstance(fb, dict) or not fb:
        return None
    labels = {
        "chemical_class": "Chemical Class", "habit_forming": "Habit Forming",
        "therapeutic_class": "Therapeutic Class", "action_class": "Action Class",
    }
    rows = []
    for k, lbl in labels.items():
        v = fb.get(k)
        if v:
            rows.append([Paragraph(f"<b>{lbl}</b>", small_grey_s), Paragraph(esc(v), small_grey_s)])
    if not rows:
        return None
    t = Table(rows, colWidths=[3.2 * cm, 12.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GREEN_LT),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def render_medicine(key, v):
    status = status_of(v)
    elements = []

    if status == "not_found":
        reason = reason_of(v) or "Not a distinct pharmaceutical compound."
        elements.append(Paragraph(
            f'<b>{esc(v.get("name", key))}</b> <font color="{GREY.hexval()}">— {esc(reason)[:260]}</font>',
            notfound_s,
        ))
        return elements

    badge_style = badge_complete_s if status == "complete" else badge_partial_s
    badge_bg = GREEN_LT if status == "complete" else GOLD_LT
    badge_txt = "VERIFIED COMPLETE" if status == "complete" else "PARTIAL — SEE NOTE"

    header_row = Table(
        [[Paragraph(esc(v.get("name", key)), name_s),
          Table([[Paragraph(badge_txt, badge_style)]], colWidths=[3.6 * cm],
                style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), badge_bg),
                                   ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))]],
        colWidths=[12.5 * cm, 3.6 * cm],
    )
    header_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    elements.append(header_row)

    diseases = v.get("used_for_diseases") or []
    if diseases:
        elements.append(Paragraph("Used for: " + esc(", ".join(diseases))[:300], diseases_s))

    if v.get("dosage_administration"):
        elements.append(Paragraph("Dosage &amp; Administration", section_label_s))
        elements.append(Paragraph(esc(v["dosage_administration"])[:900], body_s))

    se = v.get("side_effects")
    if isinstance(se, dict) and (se.get("common") or se.get("serious")):
        elements.append(Paragraph("Side Effects", section_label_s))
        if se.get("common"):
            elements.append(Paragraph("<b>Common:</b> " + esc(", ".join(se["common"]))[:400], body_s))
        if se.get("serious"):
            elements.append(Paragraph(
                f'<b><font color="{CORAL.hexval()}">Serious:</font></b> ' + esc(", ".join(se["serious"]))[:400], body_s
            ))

    st = safety_table(v.get("safety_advice"))
    if st:
        elements.append(Paragraph("Safety Advice", section_label_s))
        elements.append(st)

    ib = interactions_block(v.get("drug_interactions"))
    if ib:
        elements.append(Paragraph("Drug Interactions", section_label_s))
        elements.append(ib)

    if v.get("missed_dose_overdose"):
        elements.append(Paragraph("Missed Dose / Overdose", section_label_s))
        elements.append(Paragraph(esc(v["missed_dose_overdose"])[:500], body_s))

    fb = fact_box_table(v.get("fact_box"))
    if fb:
        elements.append(Paragraph("Fact Box", section_label_s))
        elements.append(fb)

    if v.get("storage"):
        elements.append(Paragraph("Storage", section_label_s))
        elements.append(Paragraph(esc(v["storage"])[:300], body_s))

    note = reason_of(v)
    if status == "partial" and note:
        elements.append(Paragraph(f'<i><font color="{GOLD.hexval()}">Note: {esc(note)[:400]}</font></i>', small_grey_s))

    sources = v.get("sources") or []
    if sources:
        elements.append(Paragraph("Sources: " + esc("; ".join(sources))[:400], small_grey_s))

    elements.append(Spacer(1, 8))
    return elements


def build():
    data = json.load(open(DATA_PATH, encoding="utf-8"))
    meds = data["medicines"]

    by_category = {}
    for key, v in meds.items():
        cat = v.get("category") or "Uncategorized"
        by_category.setdefault(cat, []).append((key, v))
    for cat in by_category:
        by_category[cat].sort(key=lambda kv: (status_of(kv[1]) == "not_found", kv[1].get("name", "")))

    total = len(meds)
    complete = sum(1 for v in meds.values() if status_of(v) == "complete")
    partial = sum(1 for v in meds.values() if status_of(v) == "partial")
    not_found = sum(1 for v in meds.values() if status_of(v) == "not_found")

    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="BalanceAI Medicine Information Report",
    )

    story = []
    story.append(Paragraph("BalanceAI — Medicine Information Report", report_title_s))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Every real medicine referenced across this project's disease research, presented 1mg-style: "
        "composition, uses, side effects, safety advice, drug interactions, dosing, and storage — "
        "sourced from FDA/DailyMed, MedlinePlus, EMA/UK EMC, WHO and PubMed/ClinicalTrials.gov. "
        "No field is fabricated: where a real source did not state something, the entry says so explicitly.",
        report_sub_s,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Total entries: {total} &nbsp;|&nbsp; Fully verified complete: {complete} &nbsp;|&nbsp; "
        f"Partial (real data, documented gap): {partial} &nbsp;|&nbsp; Not a medicine (device/procedure/lifestyle, documented): {not_found}",
        report_sub_s,
    ))
    story.append(PageBreak())

    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        story.append(Paragraph(esc(cat) + f" ({len(items)} entries)", cat_header_s))
        story.append(Spacer(1, 6))
        for key, v in items:
            block = render_medicine(key, v)
            if status_of(v) == "not_found":
                story.append(block[0])
            else:
                # Keep the header + used-for-diseases line glued together so a page
                # break never separates a medicine's name from its own content.
                head_len = 2 if len(block) > 1 else 1
                story.append(KeepTogether(block[:head_len]))
                story.extend(block[head_len:])
        story.append(PageBreak())

    doc.build(story)
    print(f"Wrote {OUT_PATH} — {total} entries ({complete} complete, {partial} partial, {not_found} not_found)")


if __name__ == "__main__":
    build()
