export async function requestNotificationPermission(): Promise<boolean> {
  if (typeof window === "undefined" || !("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  const result = await Notification.requestPermission();
  return result === "granted";
}

export function scheduleDailyReminder() {
  if (typeof window === "undefined") return;
  const now = new Date();
  const next = new Date();
  next.setHours(9, 0, 0, 0);
  if (next <= now) next.setDate(next.getDate() + 1);
  const delay = next.getTime() - now.getTime();
  setTimeout(() => {
    if (Notification.permission === "granted") {
      new Notification("BalanceAI — Aaj ka check-in", {
        body: "Apna daily nutrition analysis karo. 2 minute lagenge!",
        icon: "/icon-192.png",
        badge: "/icon-192.png",
      });
    }
    scheduleDailyReminder();
  }, delay);
}

export function isNotificationsSupported(): boolean {
  return typeof window !== "undefined" && "Notification" in window;
}

const FOOD_REMINDER_HOUR = 20; // 8 PM — after most people have had dinner
const MEALS_ORDER = ["Breakfast", "Lunch", "Snacks", "Dinner"] as const;

// Daily reminder to log today's meal photos (Your Medical and Food page) —
// only fires for meals not already logged, so it stops nagging once you're done.
// Uses the same client-side setTimeout approach as scheduleDailyReminder: it only
// fires while the app/tab is open at the scheduled time, same limitation as that
// one, kept consistent rather than adding real server push for a single reminder.
export function scheduleFoodPhotoReminder() {
  if (typeof window === "undefined") return;
  const now = new Date();
  const next = new Date();
  next.setHours(FOOD_REMINDER_HOUR, 0, 0, 0);
  if (next <= now) next.setDate(next.getDate() + 1);
  const delay = next.getTime() - now.getTime();

  setTimeout(async () => {
    if (Notification.permission === "granted") {
      try {
        const { getMealPhotosForDate, todayDateStr } = await import("./db");
        const logged = new Set((await getMealPhotosForDate(todayDateStr())).map((e) => e.meal));
        const missing = MEALS_ORDER.filter((m) => !logged.has(m));
        if (missing.length > 0) {
          new Notification("BalanceAI — Khana photo log karna baaki hai", {
            body: `${missing.join(", ")} ki photo abhi tak nahi li — add karo.`,
            icon: "/icon-192.png",
            badge: "/icon-192.png",
          });
        }
      } catch {
        // IndexedDB unavailable (private mode etc.) — skip silently, don't crash the timer chain.
      }
    }
    scheduleFoodPhotoReminder();
  }, delay);
}
