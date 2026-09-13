import json, pandas as pd, tabula

PDF = "/home/abhay/Downloads/medical/balanceai/data/icmr/icmr_dietary_guidelines.pdf"
OUT = "/home/abhay/Downloads/medical/balanceai/data/icmr"

tables = tabula.read_pdf(PDF, pages="all", multiple_tables=True, silent=True)

rda_table = tables[20].fillna("").astype(str)
glycemic_table = tables[47].fillna("").astype(str)
ala_table = tables[46].fillna("").astype(str)
veg_calorie = tables[42].fillna("").astype(str)
food_calorie = tables[43].fillna("").astype(str)
nutrient_comp = tables[52].fillna("").astype(str)

results = {
    "rda_nutrient_requirements": rda_table.to_dict(orient="records"),
    "glycemic_index_foods": glycemic_table.to_dict(orient="records"),
    "ala_omega3_foods": ala_table.to_dict(orient="records"),
    "vegetable_calories": veg_calorie.to_dict(orient="records"),
    "food_calories": food_calorie.to_dict(orient="records"),
    "nutrient_composition": nutrient_comp.to_dict(orient="records"),
}

with open(f"{OUT}/icmr_parsed_key_tables.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("RDA table shape:", rda_table.shape)
print("RDA columns:", list(rda_table.columns))
print("\nSample RDA rows:")
print(rda_table.head(5).to_string())
print("\nNutrient composition cols:", list(nutrient_comp.columns))
print(nutrient_comp.head(10).to_string())
print(f"\nSaved: {OUT}/icmr_parsed_key_tables.json")
