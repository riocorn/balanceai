// v2 — real bug fix: v1 was cache-first for EVERY GET request ("return
// cached || network"), which meant once a page/document was cached, every
// future visit (including a normal reload) kept serving that stale copy
// forever — a code fix on the server would never actually appear for a
// returning visitor until they manually cleared site data. Root-caused
// 2026-09-28 via a real report of a shipped header fix ("Box 1 lg:block")
// not showing live despite the dev server correctly serving the new HTML/CSS
// (confirmed with curl) — the browser's own service worker cache was the
// culprit, not the app code. Fixed with network-first for documents/data (so
// a fresh deploy is seen immediately, falling back to cache only when
// actually offline) while keeping cache-first only for /_next/static/
// chunks, which are content-hashed by Next.js — a real code change always
// gets a new hash/new URL there, so cache-first is genuinely safe for them
// and never goes stale.
const CACHE = "balanceai-v2";
const STATIC = ["/", "/dashboard", "/analyze", "/history", "/insights", "/profile", "/offline"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(STATIC)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (url.pathname.startsWith("/api/")) {
    e.respondWith(fetch(e.request).catch(() => new Response(JSON.stringify({ error: "offline" }), { headers: { "Content-Type": "application/json" } })));
    return;
  }

  // Immutable, content-hashed build assets — a real code change always
  // produces a new filename here, so cache-first is safe and never stale.
  if (url.pathname.startsWith("/_next/static/")) {
    e.respondWith(
      caches.match(e.request).then((cached) => {
        if (cached) return cached;
        return fetch(e.request).then((res) => {
          if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
          return res;
        });
      })
    );
    return;
  }

  // Everything else (HTML documents, /data/*.json, images) — network-first,
  // so a real server-side change is seen on the very next load, not one
  // visit later. Cache is only a true offline fallback now.
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
        return res;
      })
      .catch(() => caches.match(e.request).then((cached) => cached || caches.match("/offline")))
  );
});
