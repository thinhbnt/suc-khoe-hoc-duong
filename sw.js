// sw.js (Service Worker: cache tĩnh + TỰ ĐỘNG cập nhật)
//
// ⚠️ QUY TẮC BẮT BUỘC KHI SỬA CODE:
// Mỗi khi thay đổi bất kỳ file nào nằm trong danh sách ASSETS bên dưới
// (index.html, nutritionEngine.js, storage.js, manifest.json, ...), PHẢI tăng
// CACHE_NAME lên v(N+1) — ví dụ: "health-pwa-v7" -> "health-pwa-v8".
// Lý do: "activate" chỉ xoá các cache KHÁC tên CACHE_NAME; nếu giữ nguyên tên,
// bản mới ghi đè lên cache cũ và người đã cài app có thể vẫn nhận file cũ.
//
// Tên cache này PHẢI trùng hằng EXPECTED_CACHE trong index.html
// (tests/test_version_consistency.py sẽ báo lỗi nếu lệch).
//
// LUỒNG CẬP NHẬT (từ v1.4.0): install xong → self.skipWaiting() → "activate" xoá
// cache cũ + clients.claim() → tab đang mở nhận "controllerchange" và hiện banner
// "Cập nhật ngay" (xem khối "Service Worker + tự động cập nhật" trong index.html).
const CACHE_NAME = "health-pwa-v7";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./nutritionEngine.js",
  "./recommendations.js",
  "./bmiForAge.js",
  "./storage.js",
  "./foods.json"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      // Tự kích hoạt ngay: người dùng KHÔNG phải mở app 2 lần mới nhận bản mới.
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      // Dọn sạch cache của các phiên bản trước để không tốn dung lượng máy.
      .then((names) => Promise.all(
        names
          .filter((n) => n.indexOf("health-pwa-") === 0 && n !== CACHE_NAME)
          .map((n) => caches.delete(n))
      ))
      // Nhận luôn các tab đang mở (kể cả tab vẫn đang chạy code của bản cũ).
      .then(() => self.clients.claim())
      // Báo cho trang biết để vẽ lại dòng phiên bản và hiện banner cập nhật.
      .then(() => self.clients.matchAll({ type: "window" }))
      .then((clients) => clients.forEach((c) => c.postMessage({
        type: "SW_ACTIVATED",
        cache: CACHE_NAME
      })))
  );
});

// Trang có thể chủ động yêu cầu kích hoạt bản mới ngay (nút "Cập nhật ngay").
self.addEventListener("message", (e) => {
  if (e.data && e.data.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;

  // Trang HTML: ưu tiên MẠNG để luôn thấy bản mới; chỉ khi mất mạng mới dùng cache.
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          // Lưu bản mới nhất để lần mở ngoại tuyến kế tiếp vẫn có trang.
          caches.open(CACHE_NAME)
            .then((cache) => cache.put("./index.html", res.clone()))
            .catch(() => {});
          return res;
        })
        .catch(() => caches.match(e.request).then((res) => res || caches.match("./index.html")))
    );
    return;
  }

  // Tài nguyên tĩnh (js/css/ảnh/json): ưu tiên cache cho nhanh và chạy được offline.
  e.respondWith(caches.match(e.request).then((res) => res || fetch(e.request)));
});

