import tabula, json, os, pandas as pd

PDF = "/home/abhay/Downloads/medical/balanceai/data/icmr/icmr_dietary_guidelines.pdf"
OUT = "/home/abhay/Downloads/medical/balanceai/data/icmr"

tables = tabula.read_pdf(PDF, pages="all", multiple_tables=True, silent=True, pandas_options={"header": 0})
print(f"Total tables: {len(tables)}")

FOOD_KEYWORDS = ["food","nutrient","calorie","kcal","protein","fat","carb","vitamin","mineral",
                 "iron","calcium","zinc","energy","fibre","fiber","sodium","rda","requirement"]

food_tables = []
for i, df in enumerate(tables):
    if df.empty or df.shape[0] < 2:
        continue
    col_str = " ".join(str(c).lower() for c in df.columns)
    cell_str = " ".join(str(v).lower() for v in df.values.flatten()[:20])
    combined = col_str + " " + cell_str
    if any(kw in combined for kw in FOOD_KEYWORDS):
        food_tables.append({"table_index": i, "shape": list(df.shape), "columns": list(df.columns.astype(str)), "data": df.fillna("").astype(str).to_dict(orient="records")})
        print(f"  Food table {i}: {df.shape} — {list(df.columns.astype(str))[:5]}")

with open(f"{OUT}/icmr_extracted_tables.json", "w", encoding="utf-8") as f:
    json.dump(food_tables, f, indent=2, ensure_ascii=False)

print(f"\nFood-relevant tables saved: {len(food_tables)}")
print(f"Output: {OUT}/icmr_extracted_tables.json")

with open(f"{OUT}/icmr_all_tables.json", "w", encoding="utf-8") as f:
    all_data = [{"idx": i, "shape": list(df.shape), "cols": list(df.columns.astype(str)), "rows": df.fillna("").astype(str).to_dict(orient="records")} for i, df in enumerate(tables) if not df.empty]
    json.dump(all_data, f, indent=2, ensure_ascii=False)
print(f"All tables saved: {OUT}/icmr_all_tables.json")
