const CACHE_NAME = "m4b-pwa-v1";
const STATIC_ASSETS = [
  "/",
  "/static/index.html",
  "/static/style.css?v=2.2",
  "/static/app.js?v=2.2",
  "/static/manifest.json",
  "/static/icon.svg",
  "/static/icon-192.png",
  "/static/icon-512.png"
];

// Install: Cache core UI assets
self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).catch((err) => {
      console.warn("[SW] Cache addAll warning:", err);
    })
  );
});

// Activate: Clean up older caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: Pass through API and audio streaming, serve static assets
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Never intercept API routes, audio streams, or non-GET requests
  if (url.pathname.startsWith("/api/") || event.request.method !== "GET") {
    return;
  }

  // Stale-while-revalidate for static files
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
