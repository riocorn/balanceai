"""
Renders all 286,651 rows of ml_training/real_disease_symptom_data.jsonl into a
real, complete PDF -- not a sample/summary. English-only data (HPO), so no
multi-script font handling is needed (unlike generate_question_bank_pdf.py,
whose chunked-Table rendering pattern this script reuses).
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

SRC = Path(__file__).parent / "real_disease_symptom_data.jsonl"
OUT = Path(__file__).parent / "BalanceAI_Real_HPO_Disease_Symptom_Data_286651.pdf"

FONT_DIR = "/usr/share/fonts/truetype/noto"
pdfmetrics.registerFont(TTFont("NotoSans", f"{FONT_DIR}/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", f"{FONT_DIR}/NotoSans-Bold.ttf"))


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_rows():
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_doc(rows, out_path):
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=14 * mm, bottomMargin=12 * mm,
        title="BalanceAI Real HPO Disease-Symptom Data (286,651 real entries)",
    )

    header_style = ParagraphStyle("hdr", fontName="NotoSans-Bold", fontSize=7.5, textColor=colors.white, leading=9)
    cell_style = ParagraphStyle("cell", fontName="NotoSans", fontSize=7, leading=9)

    story = []
    title_style = ParagraphStyle("title", fontName="NotoSans-Bold", fontSize=16, leading=20)
    sub_style = ParagraphStyle("sub", fontName="NotoSans", fontSize=9, leading=12.5, textColor=colors.HexColor("#444444"))
    story.append(Paragraph("BalanceAI — Real HPO Disease-Symptom Data", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"{len(rows)} real disease-symptom annotation rows, source: Human Phenotype Ontology "
        f"(HPO, hpo.jax.org) -- the official, expert-curated, PMID-cited disease-phenotype "
        f"annotation database used in clinical genetics and rare-disease diagnosis worldwide. "
        f"No fabrication: every row is a real annotation downloaded directly from HPO's own "
        f"release files (phenotype.hpoa + hp.json). \"Mapped Disease ID\" shows this project's "
        f"own disease_id (from data/disease_master.json's 323 diseases) where a real match was "
        f"found; blank means the HPO disease is real but outside this project's current scope.",
        sub_style,
    ))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "License: HPO is released under a Creative Commons license (CC-BY 4.0 for the hp.json "
        "ontology; HPOA disease annotations are freely redistributable per hpo.jax.org's own "
        "terms) -- see hpo.jax.org/app/license for the exact current statement; cite "
        "\"The Human Phenotype Ontology\" (Kohler et al.) and the HPO project (hpo.jax.org) "
        "when redistributing. Generated via ml_training/build_real_hpo_dataset.py.",
        sub_style,
    ))
    story.append(Spacer(1, 10))

    col_widths = [55 * mm, 55 * mm, 18 * mm, 22 * mm, 25 * mm]
    header_row = [
        Paragraph("Disease Name", header_style), Paragraph("Symptom", header_style),
        Paragraph("HPO ID", header_style), Paragraph("PMID Reference", header_style),
        Paragraph("Mapped Disease ID", header_style),
    ]

    CHUNK = 400
    for start in range(0, len(rows), CHUNK):
        chunk = rows[start:start + CHUNK]
        table_data = [header_row]
        for r in chunk:
            table_data.append([
                Paragraph(escape_xml(r.get("disease_name", "") or "")[:200], cell_style),
                Paragraph(escape_xml(r.get("symptom", "") or "")[:200], cell_style),
                Paragraph(escape_xml(r.get("hpo_id", "") or ""), cell_style),
                Paragraph(escape_xml(r.get("reference", "") or ""), cell_style),
                Paragraph(escape_xml(r.get("balanceai_disease_id") or "—"), cell_style),
            ])
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D5C3D")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
        if start + CHUNK < len(rows):
            story.append(Spacer(1, 1))
        if (start // CHUNK) % 50 == 0:
            print(f"  built {start + len(chunk)}/{len(rows)} rows...")

    print("Building PDF (this writes all pages)...")
    doc.build(story)
    print(f"Saved: {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main():
    rows = list(load_rows())
    print(f"Loaded {len(rows)} rows")
    build_doc(rows, OUT)


if __name__ == "__main__":
    main()
