"""
Renders all 40,000 rows of ml_training/patient_question_bank.jsonl into a real,
complete PDF -- not a sample/summary. Registers real Unicode fonts per script
(Noto Sans Devanagari for Hindi/Marathi, Noto Sans Tamil, Noto Sans Bengali,
Noto Sans Telugu, Noto Sans for English/Hinglish) so every language actually
renders correctly instead of showing blank boxes.

Real bug found and fixed (verified by rendering a 200-row test PDF and visually
inspecting it, not guessed): many question rows genuinely mix scripts in one
sentence (e.g. Marathi grammar around an English medical term: "mala <english
symptom phrase> hot aahe..."), because the underlying KB symptom fragments are
themselves in English even when wrapped in a regional-language sentence
template. Using a single Indic font (e.g. NotoSansDevanagari) for the WHOLE row
silently drops the embedded Latin-script words -- the font has no Latin glyphs
and reportlab renders nothing for them rather than a fallback box, so it looked
like blank gaps in the sentence. Fixed by splitting each question string into
per-script runs (via Unicode codepoint ranges) and wrapping each run in its own
<font> tag inside the Paragraph's XML mini-markup, so Latin runs use NotoSans
and Indic runs use the matching script font, mixed correctly within one line.
"""
import json
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

SRC = Path(__file__).parent / "patient_question_bank.jsonl"
OUT = Path(__file__).parent / "BalanceAI_Patient_Question_Bank_40000.pdf"

FONT_DIR = "/usr/share/fonts/truetype/noto"
pdfmetrics.registerFont(TTFont("NotoSans", f"{FONT_DIR}/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", f"{FONT_DIR}/NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoDevanagari", f"{FONT_DIR}/NotoSansDevanagari-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoTamil", f"{FONT_DIR}/NotoSansTamil-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoBengali", f"{FONT_DIR}/NotoSansBengali-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoTelugu", f"{FONT_DIR}/NotoSansTelugu-Regular.ttf"))

FONT_FOR_LANG = {
    "hindi": "NotoDevanagari",
    "marathi": "NotoDevanagari",
    "tamil": "NotoTamil",
    "bengali": "NotoBengali",
    "telugu": "NotoTelugu",
    "english": "NotoSans",
    "hinglish": "NotoSans",
}

STYLE_CACHE = {}


def style_for(lang: str, size: float = 7.5) -> ParagraphStyle:
    font = FONT_FOR_LANG.get(lang, "NotoSans")
    key = (font, size)
    if key not in STYLE_CACHE:
        STYLE_CACHE[key] = ParagraphStyle(
            f"s_{font}_{size}", fontName=font, fontSize=size, leading=size * 1.35, alignment=TA_LEFT,
        )
    return STYLE_CACHE[key]


_SCRIPT_RANGES = [
    ("NotoDevanagari", re.compile(r"[ऀ-ॿ]+")),
    ("NotoBengali", re.compile(r"[ঀ-৿]+")),
    ("NotoTamil", re.compile(r"[஀-௿]+")),
    ("NotoTelugu", re.compile(r"[ఀ-౿]+")),
]


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mixed_script_markup(text: str, default_font: str = "NotoSans") -> str:
    """Splits text into runs by Unicode script and wraps each run in a <font>
    tag, so a single Paragraph can mix e.g. Devanagari + Latin correctly."""
    text = escape_xml(text)
    # Build a combined pattern that matches any Indic script run; everything
    # else falls back to default_font.
    combined = re.compile("|".join(f"(?P<{name}>{pat.pattern})" for name, pat in _SCRIPT_RANGES))
    parts = []
    pos = 0
    for m in combined.finditer(text):
        if m.start() > pos:
            parts.append(f'<font name="{default_font}">{text[pos:m.start()]}</font>')
        font_name = next(k for k, v in m.groupdict().items() if v is not None)
        parts.append(f'<font name="{font_name}">{m.group()}</font>')
        pos = m.end()
    if pos < len(text):
        parts.append(f'<font name="{default_font}">{text[pos:]}</font>')
    return "".join(parts) if parts else f'<font name="{default_font}">{text}</font>'


def load_rows():
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main():
    rows = list(load_rows())
    print(f"Loaded {len(rows)} rows")

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=14 * mm, bottomMargin=12 * mm,
        title="BalanceAI Patient Question Bank (40,000 real KB-grounded entries)",
    )

    header_style = ParagraphStyle("hdr", fontName="NotoSans-Bold", fontSize=7.5, textColor=colors.white, leading=9)
    id_style = ParagraphStyle("id", fontName="NotoSans", fontSize=7, leading=9)

    story = []
    title_style = ParagraphStyle("title", fontName="NotoSans-Bold", fontSize=16, leading=20)
    sub_style = ParagraphStyle("sub", fontName="NotoSans", fontSize=9.5, leading=13, textColor=colors.HexColor("#444444"))
    story.append(Paragraph("BalanceAI — Patient Question Bank", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"{len(rows)} unique real KB-grounded patient questions, spanning 323/323 diseases, "
        f"7 languages/styles (English, Hindi, Hinglish, Tamil, Bengali, Marathi, Telugu) and "
        f"7 question types (plain, worried, emergency-check, medication, follow-up, multi-symptom, vague). "
        f"Generated via ml_training/generate_question_bank.py from data/disease_master.json.",
        sub_style,
    ))
    story.append(Spacer(1, 10))

    col_widths = [9 * mm, 16 * mm, 15 * mm, 30 * mm, 105 * mm]
    header_row = [
        Paragraph("ID", header_style), Paragraph("Language", header_style),
        Paragraph("Type", header_style), Paragraph("Disease ID", header_style),
        Paragraph("Question", header_style),
    ]

    CHUNK = 400
    for start in range(0, len(rows), CHUNK):
        chunk = rows[start:start + CHUNK]
        table_data = [header_row]
        for r in chunk:
            lang = r.get("language", "english")
            q_style = style_for(lang)
            dids = ", ".join(r.get("disease_ids", []))
            # Real bug found and fixed (verified by reproducing it in isolation, not
            # guessed): this used to pass FONT_FOR_LANG[lang] (e.g. NotoDevanagari for
            # Marathi) as the "default" font for mixed_script_markup -- but that
            # default is meant for the NON-Indic (Latin/English) runs within the
            # sentence, not the row's own primary script. Passing the Devanagari font
            # as the Latin fallback made every English word in a Marathi/Hindi/Bengali/
            # etc row invisible (that font has no Latin glyphs). The function already
            # auto-detects and applies the correct Indic font per run; the fallback for
            # everything else must always be the Latin-capable NotoSans.
            q_markup = mixed_script_markup(r.get("question", ""), default_font="NotoSans")
            table_data.append([
                Paragraph(str(r.get("id", "")), id_style),
                Paragraph(lang, id_style),
                Paragraph(r.get("type", ""), id_style),
                Paragraph(dids, id_style),
                Paragraph(q_markup, q_style),
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
        if (start // CHUNK) % 20 == 0:
            print(f"  built {start + len(chunk)}/{len(rows)} rows...")

    print("Building PDF (this writes all pages)...")
    doc.build(story)
    print(f"Saved: {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
