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
