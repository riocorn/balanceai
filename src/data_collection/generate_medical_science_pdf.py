"""
Full medical-science survey report — both research passes, in full, not condensed.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import re

ROOT = Path("/home/abhay/Downloads/medical/balanceai")
OUT_PDF = ROOT / "data" / "BalanceAI_Medical_Science_Survey.pdf"

GREEN = colors.HexColor("#1d5c3d")
DARK = colors.HexColor("#0d1b1e")

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=GREEN, fontSize=20)
h2 = ParagraphStyle("h2", parent=styles["Heading1"], textColor=colors.white, fontSize=15,
                     spaceBefore=0, spaceAfter=0, backColor=GREEN, borderPadding=8)
h3 = ParagraphStyle("h3", parent=styles["Heading2"], textColor=DARK, fontSize=12.5, spaceBefore=12, spaceAfter=4)
body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14.5)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, spaceAfter=4)
link_style = ParagraphStyle("link", parent=body, fontSize=8.5, textColor=colors.HexColor("#4b5563"))


def md_to_html(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="blue">\1</link>', text)
    text = text.replace("&", "&amp;")
    text = re.sub(r"<b>&amp;", "<b>&", text)
    return text


elements = []
elements.append(Paragraph("BalanceAI — Medical Science Survey", h1))
elements.append(Paragraph(
    "Full, unedited findings from two real-source research passes (WebSearch, this session) "
    "into established nutrition/medical science relevant to the 581-dish Indian food catalog "
    "and its diet-recommendation engine. Every claim below is attributed to a real source; "
    "confidence level (well-established vs. debated vs. unsettled) is stated explicitly where "
    "the research flagged it.", body,
))
elements.append(Spacer(1, 12))

# ---------------- PASS 1 ----------------
elements.append(Paragraph("&nbsp;Research Pass 1 — Ingredients, Food Synergy, Plate Structure", h2))
elements.append(Spacer(1, 8))

pass1_sections = [
    ("1. Individual ingredient health science", [
        "**Turmeric/curcumin**: Real systematic-review-level anti-inflammatory/antioxidant evidence exists "
        "([PMC5664031](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5664031/)). Turmeric+piperine RCTs show "
        "lipid-profile benefits in cardiometabolic-risk adults "
        "([PMC12736498](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12736498/)).",
        "**Fermented foods** (idli/dosa/amboli/dhokla batters, dahi): fermentation is real, established "
        "science for improving nutrient availability — not just folklore.",
        "**Legumes/soaking**: real, well-established phytate-reduction science.",
    ]),
    ("2. Food-synergy science — with an important honesty caveat", [
        "**Turmeric + black pepper**: the famous \"2000% bioavailability\" figure traces to a single 1998 "
        "human study (20mg piperine) and has **never been independently replicated** "
        "([NanoCur](https://nanocur.com/blogs/education/reassess-piperine-curcumin-evidence), "
        "[source](https://theturmeric.co/en-us/blogs/the-root/this-mystery-ingredient-increases-turmeric-absorption-by-2000)) "
        "— real mechanism (piperine blocks curcumin glucuronidation), but the specific \"2000%\" claim is "
        "weaker evidence than usually presented.",
        "**Vitamin C + non-heme iron**: real, established mechanism (converts Fe³⁺→Fe²⁺, forms soluble "
        "chelate) — but a 2024 systematic review/meta-analysis of 11 RCTs (1,930 patients) found the clinical "
        "hemoglobin/ferritin effect \"**small and likely not clinically important**\" "
        "([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2950327224000238)) — commonly "
        "oversold as a \"2-3x boost.\"",
        "**Soaking/fermentation phytate reduction**: real, strong evidence — fermentation cuts phytates "
        ">60%, soaking+germination+fermentation combined up to 85.6% "
        "([Frontiers](https://www.frontiersin.org/journals/nutrition/articles/10.3389/fnut.2024.1478155/full)).",
        "**Cross-check against 20 real dishes read** (north/south/east/west, breakfast/lunch/dinner): Amboli "
        "and Dhoklu-style batters are explicitly fermented overnight (matches science, good); Dhuska soaks "
        "rice+chana dal before grinding (good). Andhra Chicken Curry finishes with lime (matches vitamin-C "
        "pairing, though heme iron from chicken needs this least). **Gap**: none of the turmeric-heavy dishes "
        "sampled (Kootu, Meen Curry, Andhra Chicken Curry, Ol/Yam Achaar, Shorshe Ilish) pair turmeric with "
        "black pepper specifically — a free, low-risk addition nutrition science would still endorse even "
        "given the replication caveat.",
    ]),
    ("3. Gold-standard plate structure", [
        "Harvard's Healthy Eating Plate: **50% vegetables/fruit, 25% whole grain, 25% protein** "
        "([Harvard Nutrition Source](https://nutritionsource.hsph.harvard.edu/what-should-you-eat/)) — whole "
        "grains preferred over refined, limit red/processed meat, minimize fried food.",
    ]),
    ("4. Concrete catalog critique", [
        "**Good**: Sarson da Saag (leafy-green-forward, real vegetable-heavy dish), Kootu/Bisi Bele Bath "
        "(dal+vegetable combined, whole legume base), mustard-oil-based Himachali/Bihari dishes (real "
        "high-ALA-omega3 fat choice, already verified in the nutrient DB).",
        "**Flagged by Harvard-plate standards**: a real, frequent pattern across the sample is "
        "**deep-frying** — Vegetable Kofta Curry (\"deep-fry till golden\"), Dhuska (\"deep-fry... until "
        "golden\"), Bedmi Puri, Pyaz Kachori, Misal Pav's farsan — fried items recur often enough across "
        "snack/breakfast categories that a nutrition-science-aligned system should down-weight fried "
        "preparations in ranking, not just flag them for diabetes/BP avoid-lists as the current system "
        "already does. Also, single-sabzi-per-thali (per the existing thali_types.json core_slots) likely "
        "undershoots the 50%-vegetable-by-volume target — worth a portion-side check in the optimizer, not "
        "just a nutrient-target check.",
    ]),
]

for title, bullets in pass1_sections:
    elements.append(Paragraph(title, h3))
    for b in bullets:
        elements.append(Paragraph("• " + md_to_html(b), bullet))

elements.append(PageBreak())

# ---------------- PASS 2 ----------------
elements.append(Paragraph("&nbsp;Research Pass 2 — Glycemic Response, Sodium, Fiber, Timing, Fats, Protein", h2))
elements.append(Spacer(1, 8))

pass2_sections = [
    ("1. Resistant starch / glycemic response — well-established", [
        "Cooling cooked rice/potato 24h (4°C) then optionally reheating measurably lowers postprandial "
        "glycemic response vs freshly cooked (rice: 125 vs 152 mmol·min/L glycemic response, p=0.047; "
        "potato: 12% of starch escapes digestion when cooked-then-cooled vs 3% fresh). Real, replicated "
        "across multiple studies including in type 1 diabetics.",
        "**Actionable**: dishes/cooking-notes involving rice or potato could flag \"cool before "
        "serving/refrigerate leftovers\" as a real diabetes-relevant tip.",
        "Sources: [PMC9013350](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9013350/), "
        "[PubMed 26693746](https://pubmed.ncbi.nlm.nih.gov/26693746/), "
        "[Nature Nutrition & Diabetes](https://www.nature.com/articles/s41387-022-00196-1)",
    ]),
    ("2. Sodium and hypertension — well-established, consensus", [
        "WHO: <2,000 mg sodium/day (<5g salt/day) for ALL adults, not just hypertensives. Global mean "
        "intake (~4,310 mg/day) is more than double this.",
        "**Actionable**: a concrete numeric threshold — the ranker could down-weight/flag dishes whose "
        "ingredient list is pickle/papad/namkeen-heavy against this real 2000mg/day ceiling, sharper than "
        "the current keyword-only bp_high filter.",
        "Source: [PAHO/WHO](https://www.paho.org/en/enlace/salt-intake)",
    ]),
    ("3. Fiber diversity and microbiome — well-established", [
        "~30g/day fiber target (already tracked). Additional real, distinct principle: American Gut "
        "Project found eating 30+ *different* plant species/week associates with higher microbial "
        "diversity — independent of total fiber grams.",
        "**Actionable**: current system tracks fiber quantity only; a \"distinct plant-food count over the "
        "week\" metric would be a genuinely new, separate signal, not yet built.",
        "Sources: [National Geographic](https://www.nationalgeographic.com/health/article/fiber-types-gut-microbiome-health-benefits), "
        "[Frontiers](https://www.frontiersin.org/journals/nutrition/articles/10.3389/fnut.2021.700571/full)",
    ]),
    ("4. Meal timing / circadian carb placement — NOT settled, do not act on this", [
        "Real signal exists (T2D study: breakfast-carb restriction spiked post-lunch glucose in ways "
        "dinner-restriction didn't; late eating associates with metabolic disorders) but researchers "
        "explicitly state the timing/frequency/distribution interplay \"remains poorly studied.\" "
        "Confidence: real-but-evolving. **Do not wire a \"carbs at lunch not dinner\" rule off this.**",
        "Sources: [PMC10528427](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10528427/), "
        "[MDPI Nutrients](https://www.mdpi.com/2072-6643/17/13/2135)",
    ]),
    ("5. Trans fat / vanaspati — well-established, strongest finding in this batch", [
        "WHO calls for near-total elimination of partially hydrogenated oils (industrial trans fats) "
        "globally; vanaspati measured up to 23% trans fat vs much lower in ghee/butter/refined oils. This "
        "is firmer consensus than the turmeric/vitamin-C claims already flagged in the prior pass.",
        "**Actionable now**: if \"vanaspati\" appears as a resolved ingredient anywhere in the 581-dish "
        "catalog, it should get a hard down-weight or explicit flag; ghee/mustard/groundnut oil need no "
        "such penalty. [Applied: 0.5x down-weight added to the ranker, 2026-09-14 — verified vanaspati "
        "is not currently present in the catalog, wired in defensively for future additions.]",
        "Sources: [PMC3551118](https://pmc.ncbi.nlm.nih.gov/articles/PMC3551118/), "
        "[FSSAI](https://www.fssai.gov.in/upload/uploadfiles/files/Regulation_of_TFA.pdf)",
    ]),
    ("6. Protein-combining \"myth\" — well-established, and it CONTRADICTS a common Indian nutrition assumption", [
        "Real scientific consensus (since ~2009 dietetics position statements): plant proteins do NOT need "
        "combining within the same meal (e.g., dal+rice together) — the body pools free amino acids over "
        "the day. The old \"incomplete protein\" framing is outdated.",
        "**Actionable**: if any ranking/marketing logic currently boosts \"dal+rice/roti combos for "
        "complete protein\" as a same-meal requirement, that framing should be softened — variety across "
        "the day/week matters, not pairing at every single meal.",
        "Sources: [NutritionFacts.org](https://nutritionfacts.org/video/the-protein-combining-myth/), "
        "[Wikipedia: Protein combining](https://en.wikipedia.org/wiki/Protein_combining)",
    ]),
]

for title, bullets in pass2_sections:
    elements.append(Paragraph(title, h3))
    for b in bullets:
        elements.append(Paragraph("• " + md_to_html(b), bullet))

elements.append(Spacer(1, 10))
elements.append(Paragraph("Wire-in-now vs leave-alone (from Pass 2)", h3))
elements.append(Paragraph(
    "• <b>Wire in now</b>: sodium 2000mg/day threshold, vanaspati/trans-fat hard flag (done), "
    "protein-combining myth correction if present in frontend copy<br/>"
    "• <b>Worth building, more effort</b>: 30-distinct-plants/week diversity metric, resistant-starch "
    "cooking tip for rice/potato dishes<br/>"
    "• <b>Leave alone, not settled</b>: circadian carb-timing rules", bullet,
))

doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm)
doc.build(elements)
print(f"Saved -> {OUT_PDF}")
