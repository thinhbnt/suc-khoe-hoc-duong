# Sổ Tay Sức Khỏe Học Đường — PWA

Ứng dụng web (Progressive Web App) tính chỉ số dinh dưỡng dành cho học sinh Việt Nam.
Toàn bộ thuật toán chạy **100% trên máy người dùng** (client-side), không có máy chủ, không cần
đăng ký tài khoản, không thu thập dữ liệu cá nhân.

**Bản đang chạy:** <https://thinhbnt.github.io/suc-khoe-hoc-duong/>

---

## 1. Tính năng

| Tính năng | Mô tả |
| --- | --- |
| Chỉ số BMI | Phân loại theo chuẩn WHO châu Á – Thái Bình Dương (WHO WPRO) |
| Chỉ số BMR | Công thức Mifflin–St Jeor |
| Chỉ số TDEE | `BMR × hệ số vận động` (1.2 / 1.375 / 1.55 / 1.725) |
| Calo mục tiêu | `TDEE ± 500 kcal` theo mục tiêu Giảm / Duy trì / Tăng |
| Rào chắn an toàn | Khoá thâm hụt calo với người dưới 18 tuổi và người thiếu cân; áp sàn calo sinh học |
| Hồ sơ cục bộ | Ô **Tên/Biệt danh của bạn**; mỗi lần bấm tính lưu một bản ghi vào IndexedDB |
| Sao lưu / Phục hồi | Xuất toàn bộ dữ liệu ra file `.json` và nhập lại từ file |
| Chạy offline | Service Worker cache tĩnh; cài được lên màn hình chính (chế độ `standalone`) |

Ứng dụng **không** có (ngoài phạm vi MVP): đăng ký/đăng nhập, nhập bệnh lý, đồng bộ máy chủ,
gợi ý thực đơn, xem lại lịch sử trên giao diện (dữ liệu vẫn được lưu, xem qua file sao lưu).

---

## 2. Công thức & ngưỡng

### 2.1. BMI — WHO châu Á – Thái Bình Dương

`BMI = cân nặng (kg) / chiều cao² (m)`, làm tròn 1 chữ số thập phân.

| BMI (kg/m²) | Phân loại |
| --- | --- |
| < 18.5 | Thiếu cân |
| 18.5 – 22.9 | Bình thường |
| 23.0 – 24.9 | Tiền béo phì (Thừa cân) |
| 25.0 – 29.9 | Béo phì độ I |
| ≥ 30.0 | Béo phì độ II |

### 2.2. BMR — Mifflin–St Jeor

- Nam: `10 × W + 6.25 × H − 5 × A + 5`
- Nữ: `10 × W + 6.25 × H − 5 × A − 161`

(`W` = cân nặng kg, `H` = chiều cao cm, `A` = tuổi)

### 2.3. TDEE

| Mức vận động | Giá trị | Hệ số |
| --- | --- | --- |
| Ít vận động (ngồi nhiều, học tập) | `sedentary` | 1.2 |
| Vận động nhẹ (1–3 ngày/tuần) | `light` | 1.375 |
| Vận động vừa (3–5 ngày/tuần) | `moderate` | 1.55 |
| Vận động nặng (6–7 ngày/tuần) | `very_active` | 1.725 |

### 2.4. Calo mục tiêu & rào chắn an toàn

`calo mục tiêu = TDEE + điều chỉnh`, với điều chỉnh: `lose = −500`, `maintain = 0`, `gain = +500`.

Sau đó áp dụng tuần tự 3 rào chắn:

1. **Dưới 18 tuổi** và chọn giảm cân → huỷ thâm hụt, `calo mục tiêu = TDEE` + cảnh báo.
2. **BMI < 18.5** (thiếu cân) và chọn giảm cân → huỷ thâm hụt, `calo mục tiêu = TDEE` + cảnh báo.
3. **Sàn calo sinh học**: nam < 1500 kcal → 1500; nữ < 1200 kcal → 1200 + cảnh báo.

---

## 3. Cấu trúc dự án

```
suc-khoe-hoc-duong/
├── index.html                      # Toàn bộ UI (form, kết quả, card sao lưu) + script type="module"
├── nutritionEngine.js              # Thuật toán BMI / BMR / TDEE / rào chắn an toàn
├── storage.js                      # IndexedDB + Sao lưu / Phục hồi JSON
├── sw.js                           # Service Worker cache tĩnh (chạy offline)
├── manifest.json                   # Khai báo PWA (tên, icon, standalone, theme color)
├── icon-192.png , icon-512.png     # Icon PWA (bắt buộc để cài lên màn hình chính)
├── tests/
│   └── test_nutrition_reference.py # Bộ test tham chiếu (Python) — 3 case vàng
├── .gitignore
└── README.md
```

Không dùng thư viện ngoài, không cần `npm install`, không cần bước build.

### API các module

| File | Export | Ý nghĩa |
| --- | --- | --- |
| `nutritionEngine.js` | `ACTIVITY_MULTIPLIERS`, `GOAL_ADJUSTMENTS` | Bảng hệ số |
| | `validateInput({ weight, height, age, gender, activityLevel, goal })` | Ném `Error` nếu dữ liệu ngoài khoảng hợp lệ |
| | `calculateMetrics({ ... })` | Trả `{ bmi, bmiCategory, bmr, tdee, targetCalories, warnings, calculatedAt }` |
| `storage.js` | `initDB()` | Mở/tạo DB `HealthyAppLocalDB`, xin quyền lưu trữ bền vững |
| | `saveRecord(record)` | Thêm 1 bản ghi |
| | `getAllRecords()` | Lấy toàn bộ bản ghi |
| | `exportDataToJSON()` | Tải file `suckhoe_backup_YYYY-MM-DD.json` |
| | `importDataFromJSON(file)` | Đọc file JSON và ghi vào DB |

---

## 4. Chạy thử trên máy

Ứng dụng dùng **ES module** và **Service Worker**, hai thứ này bị trình duyệt chặn khi mở bằng
`file://`. Vì vậy phải chạy qua một web server tĩnh bất kỳ:

```bash
# Cách 1: Python (có sẵn trên hầu hết máy)
python -m http.server 8000
# rồi mở http://localhost:8000

# Cách 2: Node.js
npx serve .
```

> ⚠️ Nhấp đúp vào `index.html` (giao thức `file://`) sẽ thấy trang trắng và lỗi
> *"Failed to load module script"* — đây là giới hạn của trình duyệt, không phải lỗi code.

---

## 5. Cài ứng dụng lên điện thoại

1. Mở đường link HTTPS của app bằng Chrome (Android) hoặc Safari (iOS).
2. Chọn **Thêm vào Màn hình chính** / **Cài đặt ứng dụng**.
3. Icon xuất hiện trên màn hình chính; mở lên sẽ chạy toàn màn hình, không có thanh địa chỉ.
4. Sau lần mở đầu tiên, app dùng được khi **không có mạng**.

Điều kiện kỹ thuật (đã đáp ứng): có `manifest.json` với `display: standalone`, đủ icon
192×192 và 512×512, và có Service Worker đang active.

---

## 6. Kiểm thử

```bash
python tests/test_nutrition_reference.py -v
```

Kết quả mong đợi: `Ran 3 tests ... OK`.

Bộ test đối chiếu 3 "case vàng" — nếu sửa công thức trong `nutritionEngine.js` mà làm lệch một
trong các giá trị dưới đây thì test sẽ báo lỗi:

| Case | Ghi chú | BMI | BMR | TDEE | Calo mục tiêu |
| --- | --- | --- | --- | --- | --- |
| Nam 16 tuổi, 70 kg / 170 cm, vận động nhẹ, giảm cân | bị khoá thâm hụt (dưới 18 tuổi) | 24.2 | 1688 | 2321 | **2321** |
| Nữ 20 tuổi, 40 kg / 160 cm, ít vận động, giảm cân | bị khoá thâm hụt (thiếu cân) | 15.6 | 1139 | 1367 | **1367** |
| Nam 25 tuổi, 65 kg / 172 cm, vận động vừa, giảm cân | giảm bình thường 500 kcal | 22.0 | 1605 | 2488 | **1988** |

---

## 7. ⚠️ Quy trình cập nhật code (bắt buộc)

Service Worker trong dự án **cố tình không dùng** `self.skipWaiting()` / sự kiện `activate`
(giữ đúng kiến trúc tối giản của tài liệu). Hệ quả:

> **Mỗi lần sửa `index.html`, `nutritionEngine.js`, `storage.js`, `manifest.json`
> hoặc thay icon → BẮT BUỘC tăng `CACHE_NAME` trong `sw.js`.**
>
> ```js
> const CACHE_NAME = "health-pwa-v2";   // đổi thành "health-pwa-v3", "health-pwa-v4", ...
> ```

Nếu quên bước này, người đã cài app sẽ **tiếp tục chạy bản code cũ** (vì `fetch` trả cache trước).
Sau khi tăng `CACHE_NAME` và deploy, người dùng cần mở app **2 lần** (lần 1 tải Service Worker
mới, lần 2 chạy code mới) hoặc xoá dữ liệu trang trong trình duyệt.

Quy trình chuẩn:

```bash
# 1. Sửa code
# 2. Tăng CACHE_NAME trong sw.js
# 3. Chạy test
python tests/test_nutrition_reference.py -v
# 4. Commit & deploy
git add -A
git commit -m "feat: ..."
git push origin main        # GitHub Pages tự build lại trong ~1 phút
```

---

## 8. Sao lưu & phục hồi dữ liệu

- **Sao lưu ra file JSON**: tải về `suckhoe_backup_YYYY-MM-DD.json` chứa toàn bộ bản ghi
  (`name`, `gender`, `age`, `height`, `weight`, `activityLevel`, `goal`, `bmi`, `bmiCategory`,
  `bmr`, `tdee`, `targetCalories`, `warnings`, `calculatedAt`, `id`).
- **Phục hồi từ file JSON**: chọn lại file vừa sao lưu để ghi vào máy đang dùng
  (hữu ích khi đổi điện thoại hoặc xoá dữ liệu trình duyệt).
- File không đúng định dạng (không phải mảng JSON) sẽ bị từ chối với thông báo
  *"Định dạng dữ liệu không khớp."*
- Dữ liệu được ghi **thêm** vào DB, không ghi đè — phục hồi cùng một file 2 lần sẽ tạo bản ghi trùng.

---

## 9. Quyền riêng tư

- Không có backend, không có API, không có tài khoản ⇒ không có dữ liệu nào rời khỏi thiết bị.
- Dữ liệu nằm trong IndexedDB của trình duyệt, gắn với từng máy: *ai cầm máy nào thấy dữ liệu máy đó*.
- `navigator.storage.persist()` được gọi để xin quyền lưu trữ bền vững, giảm nguy cơ hệ điều hành
  tự xoá dữ liệu khi máy hết dung lượng.
- Phù hợp tinh thần **Privacy by Design** và Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
- Xoá dữ liệu: xoá dữ liệu trang trong trình duyệt (Settings → Site data) hoặc gỡ app khỏi
  màn hình chính rồi xoá dữ liệu trang.

---

## 10. Triển khai (GitHub Pages)

Repo đã bật GitHub Pages, nguồn là nhánh `main`:

1. Push lên `main` → GitHub Pages tự build (khoảng 1 phút).
2. Truy cập <https://thinhbnt.github.io/suc-khoe-hoc-duong/>.
3. Không cần mua server hay tên miền; HTTPS có sẵn (bắt buộc để cài PWA).
   Có thể thay bằng Cloudflare Pages / Vercel / Firebase Hosting nếu muốn.

---

## 11. Miễn trừ y khoa

> Kết quả chỉ mang tính tham khảo dành cho người khỏe mạnh. Người có bệnh nền, rối loạn chuyển hóa
> hoặc đang điều trị y khoa cần tham vấn ý kiến chuyên gia dinh dưỡng.

Ứng dụng không thay thế chẩn đoán hay chỉ định của bác sĩ, và chủ động không thu thập thông tin
bệnh lý để tránh tư vấn y khoa ngoài phạm vi an toàn.



