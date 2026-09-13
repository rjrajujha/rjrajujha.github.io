const CACHE_NAME = "rj-portfolio-shell-v17";
const OFFLINE_URL = "/offline/";
const STATIC_ASSETS = [
  OFFLINE_URL,
  "/static/css/main.css",
  "/static/js/theme.js",
  "/static/js/status-modal.js",
  "/static/js/modal.js",
  "/static/js/portfolio-projects.js",
  "/static/js/docs.js",
  "/static/js/mobile-header.js",
  "/static/js/command-palette.js",
  "/static/js/site.js",
  "/static/js/chatbot.js",
  "/static/manifest.webmanifest",
  "https://rajujha.dev/favicon.ico"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) =>
        Promise.all(
          STATIC_ASSETS.map((url) =>
            cache.add(url).catch(() => undefined)
          )
        )
      )
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
  if (url.origin !== self.location.origin && url.href !== "https://rajujha.dev/favicon.ico") {
    return;
  }

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() =>
        caches.match(OFFLINE_URL).then((cached) => cached || Response.error())
      )
    );
    return;
  }

  if (!url.pathname.startsWith("/static/") && url.href !== "https://rajujha.dev/favicon.ico") {
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        fetch(req)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(req, networkResponse.clone()));
            }
          })
          .catch(() => {});
        return cached;
      }

      return fetch(req)
        .then((networkResponse) => {
          if (!networkResponse || networkResponse.status !== 200) {
            return networkResponse;
          }
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, responseClone));
          return networkResponse;
        })
        .catch(() => Response.error());
    })
  );
});
