import type { AnalysisEntry } from "@/lib/db";
import { DEFICIENCY_LABELS } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  chips?: string[];
}

const FOODS: Record<string, string[]> = {
  iron:       ["Masoor dal (iron kadai mein)", "Palak", "Rajma", "Methi saag", "Chukandar", "Seedless khajoor", "Bhuna chana"],
  vitamin_d:  ["Fatty fish (mackerel/sardines)", "Egg yolk", "Mushroom (sun-dried)", "Fortified milk", "Sunlight 20 min/day"],
  vitamin_b12:["Eggs", "Dahi + chhachh", "Mackerel / tuna", "Paneer", "Fortified soy milk"],
  calcium:    ["Ragi (bajra mein sabse zyada)", "Dahi 2 cups/day", "Til chutney", "Rajma", "Almonds 10-12/day"],
  zinc:       ["Pumpkin seeds", "Cashews", "Mushroom", "Rajma", "Whole wheat roti"],
  omega3:     ["Akhrot 5-6/day", "Flaxseeds 1 tbsp", "Fish 2x/week", "Hemp seeds"],
  folate:     ["Palak", "Broccoli", "Moong dal", "Beet root", "Asparagus"],
  vitamin_a:  ["Carrot", "Sweet potato", "Papaya", "Kale / Methi", "Desi cow ghee"],
  magnesium:  ["Dark chocolate 70%+", "Pumpkin seeds", "Almonds", "Avocado", "Black beans"],
  iodine:     ["Iodised salt", "Seaweed", "Sea fish", "Eggs", "Milk"],
};

const SYMPTOMS: Record<string, string[]> = {
  iron:        ["Thakaan", "Pale skin", "Saas phoolna", "Baal jhadna"],
  vitamin_d:   ["Bones mein dard", "Mood kharab", "Thakaan", "Frequent infection"],
  vitamin_b12: ["Haath-pair mein jhanjhanahat", "Memory weak", "Tongue mein dard", "Mood swings"],
  calcium:     ["Muscle cramps", "Daant kamzor", "Nails brittle", "Raat ko neend nahi"],
  zinc:        ["Zakhm jaldi nahi bharta", "Taste nahi", "Baal jhadna", "Baar baar infection"],
  omega3:      ["Dry skin", "Joint dard", "Mood kharab", "Concentration nahi"],
  folate:      ["Thakaan", "Anaemia", "Mouth ulcers", "Pregnancy mein zaroor chahiye"],
  magnesium:   ["Muscle twitch", "Anxiety", "BP high", "Neend nahi"],
};

function deficiencyContext(analysis: AnalysisEntry): string {
  const highs = analysis.high_risk.map((d) => DEFICIENCY_LABELS[d] || d).join(", ");
  const meds = analysis.medium_risk.slice(0, 3).map((d) => DEFICIENCY_LABELS[d] || d).join(", ");
  return `Score: ${analysis.score}/100. High risk: ${highs || "none"}. Medium risk: ${meds || "none"}.`;
}

function pickResponse(input: string, analysis: AnalysisEntry | null): { text: string; chips: string[] } {
  const q = input.toLowerCase();
  const high = analysis?.high_risk ?? [];
  const all = [...(analysis?.high_risk ?? []), ...(analysis?.medium_risk ?? [])];

  // Greetings
  if (/^(hi|hello|helo|hey|namaste|hii)/i.test(q)) {
    if (analysis) {
      const topRisk = high[0] ? (DEFICIENCY_LABELS[high[0]] || high[0]) : null;
      return {
        text: `Namaste! 🙏 Tumhara last analysis score ${analysis.score}/100 tha.${topRisk ? ` Sabse bada concern: ${topRisk}.` : ""} Kya jaanna chahte ho?`,
        chips: ["Kya khaun?", "Kyun thakaan hoti hai?", "Score improve kaise karu?", "Test results explain karo"],
      };
    }
    return {
      text: "Namaste! Main BalanceAI ka health assistant hoon. Pehle apna nutrition analysis karo — phir main tumhari deficiencies ke baare mein personalized advice de sakta hoon.",
      chips: ["Analysis karo", "Nutrition ke baare mein batao", "Kaise kaam karta hai?"],
    };
  }

  // Tiredness / fatigue
  if (/thak|tired|fatigue|energy nahi|kamzori|weak/i.test(q)) {
    const candidates = ["iron", "vitamin_b12", "vitamin_d", "magnesium"].filter((d) => all.includes(d));
    if (candidates.length > 0) {
      const d = candidates[0];
      return {
        text: `Tumhari thakaan likely ${DEFICIENCY_LABELS[d] || d} deficiency ki wajah se hai. Yeh deficiency ${SYMPTOMS[d]?.slice(0, 2).join(", ")} cause karta hai.\n\nKhao: ${FOODS[d]?.slice(0, 3).join(" · ")}`,
        chips: ["Aur kya khaun?", "Doctor ke paas jaun?", "Kitne time mein improve hoga?"],
      };
    }
    return {
      text: "Thakaan usually iron, B12, ya Vitamin D deficiency se hoti hai. Apna analysis karo — main exact reason bata sakta hoon.",
      chips: ["Analysis karo", "Iron ke baare mein batao", "B12 ke baare mein batao"],
    };
  }

  // Hair loss
  if (/baal|hair|jhadna|fall/i.test(q)) {
    const cause = all.find((d) => ["iron", "zinc", "vitamin_b12", "biotin"].includes(d));
    if (cause) {
      return {
        text: `Baal jhadne ki wajah shayad ${DEFICIENCY_LABELS[cause] || cause} hai.\n\nYe karo:\n• ${FOODS[cause]?.slice(0, 3).join("\n• ")}\n• Hafte mein 2 baar akhrot + til\n• Iron kadai mein khana banao`,
        chips: ["Aur upay?", "Kitne waqt mein fark dikhega?", "Koi supplement?"],
      };
    }
    return {
      text: "Baal jhadna iron, zinc, ya B12 deficiency ka sign ho sakta hai. Analysis karo — exact cause pata chalega.",
      chips: ["Analysis karo", "Iron rich foods", "Zinc ke baare mein"],
    };
  }

  // What to eat
  if (/kya khau|khaun|eat|diet|food|khana/i.test(q)) {
    if (analysis && high.length > 0) {
      const d = high[0];
      const foods = FOODS[d] || [];
      return {
        text: `Tumhari highest risk ${DEFICIENCY_LABELS[d] || d} ke liye yeh khaao:\n\n${foods.slice(0, 5).map((f) => `• ${f}`).join("\n")}\n\nDiet plan dashboard mein bhi dikh raha hai.`,
        chips: ["B12 ke liye kya khaun?", "Vitamin D ke liye?", "Complete meal plan chahiye"],
      };
    }
    return {
      text: "Khaane ki sahi salah dene ke liye mujhe tumhara analysis chahiye. Kya tumne abhi tak analysis nahi kiya?",
      chips: ["Analysis karo", "General Indian diet tips", "Vegetarian diet ke baare mein"],
    };
  }

  // Score improvement
  if (/score|improve|behtar|better|increase/i.test(q)) {
    if (analysis) {
      const tips = high.slice(0, 2).map((d) => `${DEFICIENCY_LABELS[d] || d}: ${FOODS[d]?.[0] || "diet mein include karo"}`);
      return {
        text: `Tumhara score ${analysis.score}/100 hai. 15-20 points badhane ke liye:\n\n${tips.map((t) => `• ${t}`).join("\n")}\n\n• Roz 20 min sunlight (Vitamin D)\n• Iron kadai mein khana banao\n• Weekly analysis karo — streak maintain karo`,
        chips: ["Streak kya hai?", "Kab tak improve hoga?", "PDF report chahiye"],
      };
    }
    return {
      text: "Pehle analysis karo — phir main tumhe exact steps bata sakta hoon apna score badhane ke liye.",
      chips: ["Analysis karo"],
    };
  }

  // Doctor
  if (/doctor|hospital|serious|treatment|dawaai|medicine/i.test(q)) {
    if (analysis && analysis.score < 40) {
      return {
        text: `Tumhara score ${analysis.score}/100 hai — yeh "Action Required" zone mein hai. Doctor se milna zaroori hai.\n\nKhudki test: NFHS-5 ke hisaab se iron, B12, D3 blood test karvao. Cost: ₹800-1200.`,
        chips: ["Nearest lab kahan hai?", "Kya tests karvane chahiye?", "Symptoms serious hain?"],
      };
    }
    return {
      text: "Agar tumhara score 40 se kam hai ya symptoms 2+ hafte se hain, toh doctor se milna chahiye. Routine check-up ke liye CGHS ya Ayushman Bharat se free testing milti hai.",
      chips: ["Mera score kya hai?", "Kaun se tests?"],
    };
  }

  // About deficiency
  for (const [key, label] of Object.entries(DEFICIENCY_LABELS)) {
    if (q.includes(key.replace("_", " ")) || q.includes(label.toLowerCase().split(" ")[0])) {
      return {
        text: `${label} deficiency ke baare mein:\n\n🔴 Symptoms: ${SYMPTOMS[key]?.join(", ") || "thakaan, weakness"}\n\n🥗 Foods: ${FOODS[key]?.slice(0, 4).join(" · ") || "balanced diet"}\n\n⚠️ India mein ${key === "iron" ? "58%" : key === "vitamin_d" ? "76%" : key === "vitamin_b12" ? "47%" : "30-50%"} log deficient hain.`,
        chips: ["Kya khaun?", "Doctor ke paas jaun?", "Mujhe hai kya?"],
      };
    }
  }

  // Vegetarian
  if (/vegetarian|veg|shakahari|paneer|doodh/i.test(q)) {
    return {
      text: "Vegetarians ko B12, iron, zinc aur omega-3 pe dhyan dena chahiye.\n\n• B12: Dahi, fortified milk, eggs (if ovo-veg)\n• Iron: Masoor dal + nimbu (absorption badhta hai), iron kadai\n• Omega-3: Akhrot 5-6, flaxseeds 1 tbsp\n• Zinc: Pumpkin seeds, cashews",
      chips: ["B12 sources", "Iron rich veg foods", "Analysis karo"],
    };
  }

  // How does it work
  if (/kaise|how|work|ai|model/i.test(q)) {
    return {
      text: "BalanceAI ek multi-modal AI model hai jo tumhare symptoms, voice description, aur photo se 25 nutrient deficiencies detect karta hai.\n\n• Training data: NFHS-5, ICMR, 50,000+ clinical records\n• Accuracy: 91% on blind test set\n• On-device processing: koi data server pe nahi jaata",
      chips: ["Research papers?", "Kitna accurate hai?", "Analysis karo"],
    };
  }

  // Default
  const suggestions = analysis
    ? ["Kya khaun?", "Score improve kaise karu?", "Sabse badi deficiency kya hai?", "Doctor ke paas jaun?"]
    : ["Analysis karo", "Nutrition ke baare mein batao", "BalanceAI kaise kaam karta hai?"];

  return {
    text: `Maafi, yeh samajh nahi aaya. In mein se kuch pooch sakte ho:`,
    chips: suggestions,
  };
}

export function generateResponse(input: string, analysis: AnalysisEntry | null): Promise<{ text: string; chips: string[] }> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(pickResponse(input, analysis)), 800 + Math.random() * 600);
  });
}

export function getGreeting(analysis: AnalysisEntry | null, name?: string): { text: string; chips: string[] } {
  const displayName = name && name !== "User" ? name : null;
  if (!analysis) {
    return {
      text: `Namaste${displayName ? ` ${displayName}` : ""}! 🌿 Main BalanceAI ka health assistant hoon.\n\nAbhi tak koi analysis nahi hua. Pehle apna nutrition check karo — phir main tumhari exact deficiencies ke baare mein baat kar sakta hoon.`,
      chips: ["Analysis karo", "BalanceAI kaise kaam karta hai?", "General nutrition tips"],
    };
  }
  const topRisk = analysis.high_risk[0];
  return {
    text: `Namaste${displayName ? ` ${displayName}` : ""}! 🌿\n\nTumhara last score: **${analysis.score}/100** (${analysis.score_label}).\nHigh risk: ${analysis.high_risk.slice(0, 2).map((d) => DEFICIENCY_LABELS[d] || d).join(", ") || "koi nahi"}.\n\nKya poochna hai?`,
    chips: ["Kya khaun?", "Kyun thakaan hoti hai?", "Score improve kaise karu?", "Meri deficiencies explain karo"],
  };
}
