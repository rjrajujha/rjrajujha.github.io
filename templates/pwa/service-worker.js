const CACHE_NAME = "rj-portfolio-shell-v2";
const OFFLINE_URL = "/offline/";
const STATIC_ASSETS = [
  OFFLINE_URL,
  "/static/css/main.css",
  "/static/js/theme.js",
  "/static/js/modal.js",
  "/static/js/site.js",
  "/static/js/chatbot.js",
  "/static/manifest.webmanifest",
  "/static/favicon/favicon.ico",
  "/static/favicon/favicon-32x32.png",
  "/static/favicon/favicon-16x16.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  if (req.method !== "GET") {
    return;
  }

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  if (!url.pathname.startsWith("/static/")) {
    return;
  }

  event.respondWith(
    fetch(req)
      .then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
          return networkResponse;
        }

        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, responseClone));
        return networkResponse;
      })
      .catch(() =>
        caches.match(req).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(req);
        })
      )
  );
});
