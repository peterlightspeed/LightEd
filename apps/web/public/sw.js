/* LightEd service worker — small on purpose.
 * - Precaches the offline page + icons.
 * - Static assets (/_next/static, images): cache-first.
 * - Page navigations: network-first, falling back to /offline.html when there is no connection.
 * - API calls (other origin) are NEVER cached, so data is always live and private.
 * Bump VERSION to invalidate old caches after a deploy. */
const VERSION = "lighted-v1";
const PRECACHE = ["/offline.html", "/icon-192.png", "/logo-mark.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return; // skip API + third parties

  if (req.mode === "navigate") {
    e.respondWith(fetch(req).catch(() => caches.match("/offline.html")));
    return;
  }
  if (url.pathname.startsWith("/_next/static/") || /\.(png|jpg|svg|ico|woff2?)$/.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(
        (hit) =>
          hit ||
          fetch(req).then((res) => {
            const copy = res.clone();
            caches.open(VERSION).then((c) => c.put(req, copy));
            return res;
          })
      )
    );
  }
});
