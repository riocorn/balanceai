// Prevalence (%) — based on NFHS-5 (2019-21), NNMB 2012, ICMR guidelines

export const NATIONAL_PREVALENCE: Record<string, number> = {
  iron:        57,
  omega3:      54,
  vitamin_b12: 47,
  calcium:     49,
  vitamin_d:   42,
  zinc:        37,
  folate:      33,
  vitamin_a:   24,
  magnesium:   29,
  iodine:      18,
};

export const DEFICIENCY_DESCRIPTIONS: Record<string, string> = {
  iron:        "Iron deficiency anaemia is India's most prevalent micronutrient deficiency, especially in women and children.",
  omega3:      "Omega-3 deficiency is high due to low fish consumption in most Indian states and poor ALA conversion.",
  vitamin_b12: "B12 deficiency is rampant due to predominantly vegetarian diets and low dairy absorption.",
  calcium:     "Calcium intake is well below RDA in most Indian states; dairy consumption is insufficient.",
  vitamin_d:   "Despite abundant sunlight, indoor lifestyles and skin pigmentation limit Vitamin D synthesis.",
  zinc:        "Zinc deficiency from phytate-rich cereal diets reduces absorption across North India.",
  folate:      "Folate deficiency is critical in pregnant women; limited green vegetable intake is the key driver.",
  vitamin_a:   "VAD persists in children under 5 in high-burden states, linked to low dietary diversity.",
  magnesium:   "Soil depletion and processed food consumption drive magnesium deficiency across urban populations.",
  iodine:      "Iodine deficiency has reduced significantly since the Universal Salt Iodization program.",
};

export type StatePrevalence = Record<string, number>;

export const STATE_PREVALENCE: Record<string, StatePrevalence> = {
  "Bihar":           { iron: 68, omega3: 58, vitamin_b12: 52, calcium: 56, vitamin_d: 46, zinc: 44, folate: 41, vitamin_a: 35, magnesium: 34, iodine: 26 },
  "UP":              { iron: 65, omega3: 55, vitamin_b12: 50, calcium: 54, vitamin_d: 44, zinc: 42, folate: 39, vitamin_a: 32, magnesium: 32, iodine: 24 },
  "Rajasthan":       { iron: 63, omega3: 57, vitamin_b12: 53, calcium: 52, vitamin_d: 45, zinc: 40, folate: 36, vitamin_a: 30, magnesium: 31, iodine: 22 },
  "MP":              { iron: 62, omega3: 56, vitamin_b12: 49, calcium: 53, vitamin_d: 43, zinc: 41, folate: 38, vitamin_a: 29, magnesium: 30, iodine: 23 },
  "Odisha":          { iron: 61, omega3: 48, vitamin_b12: 44, calcium: 51, vitamin_d: 41, zinc: 39, folate: 35, vitamin_a: 28, magnesium: 30, iodine: 22 },
  "Assam":           { iron: 60, omega3: 46, vitamin_b12: 46, calcium: 50, vitamin_d: 40, zinc: 38, folate: 34, vitamin_a: 27, magnesium: 29, iodine: 21 },
  "West Bengal":     { iron: 58, omega3: 44, vitamin_b12: 48, calcium: 49, vitamin_d: 40, zinc: 36, folate: 32, vitamin_a: 24, magnesium: 28, iodine: 19 },
  "Haryana":         { iron: 56, omega3: 55, vitamin_b12: 47, calcium: 48, vitamin_d: 43, zinc: 36, folate: 31, vitamin_a: 22, magnesium: 28, iodine: 17 },
  "Delhi":           { iron: 54, omega3: 56, vitamin_b12: 50, calcium: 47, vitamin_d: 44, zinc: 35, folate: 30, vitamin_a: 20, magnesium: 29, iodine: 16 },
  "Gujarat":         { iron: 55, omega3: 57, vitamin_b12: 51, calcium: 46, vitamin_d: 42, zinc: 36, folate: 31, vitamin_a: 22, magnesium: 27, iodine: 17 },
  "Telangana":       { iron: 57, omega3: 46, vitamin_b12: 46, calcium: 48, vitamin_d: 40, zinc: 37, folate: 33, vitamin_a: 23, magnesium: 28, iodine: 17 },
  "Andhra Pradesh":  { iron: 56, omega3: 45, vitamin_b12: 45, calcium: 47, vitamin_d: 39, zinc: 36, folate: 32, vitamin_a: 22, magnesium: 27, iodine: 17 },
  "Maharashtra":     { iron: 54, omega3: 52, vitamin_b12: 46, calcium: 46, vitamin_d: 41, zinc: 35, folate: 31, vitamin_a: 21, magnesium: 27, iodine: 16 },
  "Karnataka":       { iron: 52, omega3: 48, vitamin_b12: 44, calcium: 45, vitamin_d: 40, zinc: 34, folate: 30, vitamin_a: 20, magnesium: 26, iodine: 16 },
  "Punjab":          { iron: 50, omega3: 52, vitamin_b12: 44, calcium: 44, vitamin_d: 43, zinc: 33, folate: 28, vitamin_a: 18, magnesium: 26, iodine: 15 },
  "Tamil Nadu":      { iron: 49, omega3: 42, vitamin_b12: 43, calcium: 44, vitamin_d: 38, zinc: 32, folate: 28, vitamin_a: 18, magnesium: 25, iodine: 15 },
  "Kerala":          { iron: 43, omega3: 38, vitamin_b12: 41, calcium: 40, vitamin_d: 35, zinc: 28, folate: 24, vitamin_a: 14, magnesium: 22, iodine: 13 },
};

export const SEASONAL_TIPS: Record<number, { title: string; deficiencies: string[]; tip: string }> = {
  0:  { title: "January — Winter Peak", deficiencies: ["vitamin_d", "iron", "vitamin_c"], tip: "Sardiyron mein sun exposure kam hota hai — subah ki dhoop lo aur iron-rich khana khao." },
  1:  { title: "February — Late Winter", deficiencies: ["vitamin_d", "calcium", "magnesium"], tip: "Calcium aur D3 ka combo important hai — doodh, dahi, aur thodi dhoop." },
  2:  { title: "March — Spring Start", deficiencies: ["iron", "folate", "vitamin_b12"], tip: "Spring fatigue real hai — green leafy vegetables aur B12 pe focus karo." },
  3:  { title: "April — Summer Onset", deficiencies: ["magnesium", "potassium", "vitamin_c"], tip: "Garmi mein electrolytes bahut zaruri — coconut water, banana, nimbu paani." },
  4:  { title: "May — Peak Summer", deficiencies: ["magnesium", "potassium", "zinc"], tip: "Paseena se minerals kho jaate hain — hydrated raho aur mineral-rich khana khao." },
  5:  { title: "June — Pre-Monsoon", deficiencies: ["vitamin_c", "zinc", "vitamin_d"], tip: "Immunity strengthen karo monsoon se pehle — amla, aam, nimbu zyada lo." },
  6:  { title: "July — Monsoon", deficiencies: ["vitamin_c", "vitamin_d", "iodine"], tip: "Barish mein sun exposure zero hota hai — D3 supplement lo aur iodized namak use karo." },
  7:  { title: "August — Deep Monsoon", deficiencies: ["vitamin_d", "vitamin_c", "iron"], tip: "Gut infections immune system weaken karte hain — probiotic khana khaao, curd, kanji." },
  8:  { title: "September — Post-Monsoon", deficiencies: ["vitamin_d", "vitamin_c", "zinc"], tip: "Monsoon ke baad immunity dip hota hai — dhoop shuru ho rahi hai, vitamin D recover hoga." },
  9:  { title: "October — Festive Season", deficiencies: ["iron", "omega3", "vitamin_b12"], tip: "Tyohaar ke khane mein processed food zyada hota hai — balance maintain karo." },
  10: { title: "November — Winter Approach", deficiencies: ["vitamin_d", "omega3", "calcium"], tip: "Sardiyaan shuru — omega-3 rich foods lo aur D3 supplement consider karo." },
  11: { title: "December — Full Winter", deficiencies: ["vitamin_d", "iron", "vitamin_b12"], tip: "Sardi mein outdoor time kam hota hai — active raho aur iron + B12 check karo." },
};

export function getSeasonalTip() {
  return SEASONAL_TIPS[new Date().getMonth()];
}

export function getStateData(state: string): StatePrevalence | null {
  return STATE_PREVALENCE[state] ?? null;
}
