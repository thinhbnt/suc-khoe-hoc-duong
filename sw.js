// sw.js (Service Worker lưu cache tĩnh)
//
// ⚠️ QUY TẮC BẮT BUỘC KHI SỬA CODE:
// Mỗi khi thay đổi bất kỳ file nào nằm trong danh sách ASSETS bên dưới
// (index.html, nutritionEngine.js, storage.js, manifest.json, ...), PHẢI tăng
// CACHE_NAME lên v(N+1) — ví dụ: "health-pwa-v3" -> "health-pwa-v4".
// Lý do: Service Worker này không có bước "activate" + skipWaiting (giữ đúng
// kiến trúc trong tài liệu), nên trình duyệt KHÔNG tự xoá cache cũ. Nếu giữ
// nguyên tên cache, người đã cài app sẽ tiếp tục chạy bản code cũ.
const CACHE_NAME = "health-pwa-v3";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./nutritionEngine.js",
  "./recommendations.js",
  "./storage.js",
  "./foods.json"
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
