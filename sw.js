// sw.js (Service Worker lưu cache tĩnh)
const CACHE_NAME = "health-pwa-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./nutritionEngine.js",
  "./storage.js"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
