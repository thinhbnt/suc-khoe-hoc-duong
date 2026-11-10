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
| BMI theo tuổi | Với 10–19 tuổi: **z-score + bách phân vị** theo WHO Growth Reference 2007 (5 nhóm chuẩn thiếu niên) |
| Chỉ số BMR | Công thức Mifflin–St Jeor |
| Chỉ số TDEE | `BMR × hệ số vận động` (1.2 / 1.375 / 1.55 / 1.725) |
| Calo mục tiêu | `TDEE ± 500 kcal` theo mục tiêu Giảm / Duy trì / Tăng |
| Rào chắn an toàn | Khoá thâm hụt calo với người dưới 18 tuổi và người thiếu cân; áp sàn calo sinh học |
| Hồ sơ cục bộ | Ô **Tên/Biệt danh của bạn**; mỗi lần bấm tính lưu một bản ghi vào IndexedDB |
| Lịch sử & biểu đồ | Danh sách các lần đo đã lưu + biểu đồ SVG xu hướng BMI (vẽ tay, không dùng thư viện) |
| Xoá dữ liệu | Xoá từng lần đo hoặc xoá toàn bộ ngay trong app (bấm 2 lần để tránh nhầm) |
| Gợi ý khẩu phần | Chia calo mục tiêu theo tỷ lệ bữa **30 / 40 / 30** và gợi ý món Việt cụ thể cho từng bữa |
| Khuyến cáo vận động | Theo nhóm tuổi (dưới 18 / 18–64 / từ 65), tham khảo WHO 2020 |
| Sao lưu / Phục hồi | Xuất toàn bộ dữ liệu ra file `.json` và nhập lại từ file |
| Chạy offline | Service Worker cache tĩnh; cài được lên màn hình chính (chế độ `standalone`) |
| Thân thiện | Tự chuyển giao diện tối theo cài đặt máy; lỗi nhập liệu hiện ngay trong form thay vì `alert()`; `aria-live` / `role` cho trình đọc màn hình |
| Phiên bản | Footer hiển thị **số phiên bản + ngày build + tên bộ nhớ đệm đang chạy**, giúp biết ngay máy đã nhận bản mới chưa (không cần xoá dữ liệu trang) |

Ứng dụng **không** có (ngoài phạm vi): đăng ký/đăng nhập, nhập bệnh lý, đồng bộ máy chủ,
thực đơn cá nhân hoá theo bệnh lý/dị ứng/ngân sách, nhật ký ăn uống hằng ngày.

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

### 2.5. Chia bữa 30 / 40 / 30

`splitMeals(calo mục tiêu)` chia calo mục tiêu cho 3 bữa:

| Bữa | Tỷ lệ | Công thức |
| --- | --- | --- |
| Sáng | 30 % | `Math.round(calo × 0.3)` |
| Trưa | 40 % | `Math.round(calo × 0.4)` |
| Tối | 30 % | `calo − sáng − trưa` (nhận phần dư để **tổng 3 bữa luôn bằng calo mục tiêu**) |

Ví dụ calo mục tiêu 2321 kcal → sáng **696**, trưa **928**, tối **697** (tổng = 2321).

Sau khi có ngân sách từng bữa, `buildMealPlan()` chọn món từ `foods.json` theo thứ tự:

1. Một **món chính trọn bữa** (phở, bánh mì, xôi, bánh cuốn, bún chả) nếu nó chiếm ≥ 55 %
   ngân sách bữa; nếu không thì **1 món tinh bột + 1 món đạm**.
2. Tối đa **2 món rau / trái cây**.
3. Tối đa **2 món bổ sung** (sữa, hạt, chất béo) khi còn ≥ 60 kcal.
4. Nếu vẫn dư ≥ 150 kcal → thêm **1 khẩu phần đạm** (hoặc tinh bột).

Mọi món đều được chọn sao cho **tổng ≤ ngân sách bữa**; phần dư được hiển thị minh bạch
(*"Còn X kcal – có thể thêm …"*) chứ không tự bịa thêm món.

### 2.6. Khuyến cáo vận động (tham khảo WHO 2020)

| Nhóm tuổi | Khuyến cáo chính |
| --- | --- |
| 10 – 17 | Trung bình–mạnh **≥ 60 phút/ngày**; ≥ 3 ngày/tuần hoạt động mạnh; hạn chế thời gian trước màn hình |
| 18 – 64 | **150–300 phút/tuần** trung bình, hoặc 75–150 phút/tuần mạnh; tập sức mạnh ≥ 2 ngày/tuần |
| 65 – 100 | Như trên + bài tập **thăng bằng ≥ 3 ngày/tuần** để giảm nguy cơ té ngã |

Khuyến cáo này **độc lập** với dropdown "Mức độ vận động" — dropdown chỉ dùng để nhân hệ số TDEE.

### 2.7. BMI theo tuổi — WHO Growth Reference 2007 (10–19 tuổi)

Ngưỡng BMI tuyệt đối ở §2.1 là chuẩn cho **người trưởng thành**. Trẻ đang lớn có BMI trung bình
thay đổi theo từng tuổi và giới, nên WHO khuyến nghị so **theo tuổi** bằng z-score / bách phân vị
thay vì so với một con số cố định. Vì vậy với tuổi **10–19**, app hiển thị thêm ô "Phân loại theo tuổi".

**Dữ liệu:** bảng LMS (L, M, S) của WHO, trích tháng tuổi 120–229 cho nam và nữ, lấy từ kho chính
thức <https://github.com/WorldHealthOrganization/anthroplus>
(`data-raw/growthstandards/bfawho2007.txt`).

**Công thức:**

- `z = ((BMI / M)^L − 1) / (L × S)`
- Ngoài khoảng ±3 SD, dùng đúng cách WHO hiệu chỉnh (nội suy tuyến tính theo khoảng cách SD2–SD3),
  nhờ vậy kết quả trùng khớp 100 % với phần mềm WHO AnthroPlus (919/919 ca kiểm chứng).
- Bách phân vị = `Φ(z) × 100` (xấp xỉ hàm phân phối chuẩn, Abramowitz & Stegun 7.1.26).

| z-score | Nhóm |
| --- | --- |
| < −3 | Gầy nặng |
| −3 … < −2 | Gầy |
| −2 … +1 | Bình thường |
| > +1 … +2 | Thừa cân |
| > +2 | Béo phì |

**Ví dụ:** nam 16 tuổi, 70 kg / 170 cm → BMI 24.2

- Theo người lớn (WPRO): *Tiền béo phì (Thừa cân)*
- Theo tuổi (WHO 2007): z = **1.18**, bách phân vị **88.2** → *Thừa cân*; trung vị BMI của nam 16 tuổi là 20.5 kg/m²

Hai cách phân loại hiển thị **song song** để thấy rõ khác biệt; từ 18 tuổi app ghi chú thêm rằng
ngưỡng người lớn được dùng để tham khảo song song. Ngoài khoảng 10–19 tuổi, ô này tự ẩn.

---

## 3. Cấu trúc dự án

```
suc-khoe-hoc-duong/
├── index.html                      # UI (form, kết quả, BMI theo tuổi, gợi ý khẩu phần, lịch sử, sao lưu) + script type="module"
├── nutritionEngine.js              # Thuật toán BMI / BMR / TDEE / rào chắn an toàn / chia bữa 30-40-30
├── bmiForAge.js                    # z-score & bách phân vị BMI theo tuổi — bảng LMS WHO 2007 (10-19 tuổi)
├── recommendations.js              # Gợi ý khẩu phần theo ngân sách bữa + khuyến cáo vận động theo tuổi
├── foods.json                      # Dữ liệu 35 món Việt (kcal / khẩu phần / nhóm / bữa phù hợp)
├── storage.js                      # IndexedDB + xoá bản ghi + Sao lưu / Phục hồi JSON
├── sw.js                           # Service Worker cache tĩnh (chạy offline)
├── manifest.json                   # Khai báo PWA (tên, icon, standalone, theme color)
├── icon-192.png , icon-512.png     # Icon PWA (bắt buộc để cài lên màn hình chính)
├── tests/
│   ├── test_nutrition_reference.py # Bộ test tham chiếu (Python) — 3 case vàng BMI/BMR/TDEE
│   ├── test_food_data.py           # Test dữ liệu foods.json + tỷ lệ chia bữa 30/40/30
│   ├── test_bmi_for_age.py         # Test bảng LMS + z-score khớp dữ liệu WHO 2007
│   ├── test_version_consistency.py # Test phiên bản app ↔ CACHE_NAME của Service Worker ↔ module được cache
│   └── fixtures/
│       ├── bfawho2007.txt          # Bảng LMS gốc của WHO (nguyên văn, 340 dòng)
│       └── who2007_zbmi_sample.csv # 12 ca (BMI, tuổi tháng, z) do WHO AnthroPlus tính
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
| | `MEAL_SPLIT`, `MEAL_LABELS` | Tỷ lệ 0.3 / 0.4 / 0.3 và nhãn "Bữa sáng / trưa / tối" |
| | `splitMeals(targetCalories)` | Trả `{ breakfast, lunch, dinner }`, tổng luôn bằng `targetCalories` |
| `recommendations.js` | `loadFoods()` | `fetch('./foods.json')` và cache trong bộ nhớ |
| | `buildMealPlan(mealKey, budgetKcal, foods)` | Trả `{ meal, budgetKcal, items[], totalKcal, remainingKcal }` |
| | `getActivityAdvice(age)` | Trả `{ group, headline, details[], source }` hoặc `null` nếu tuổi ngoài 10–100 |
| `bmiForAge.js` | `LMS_BMI_FOR_AGE`, `WHO_BMI_CATEGORIES`, `WHO_BMI_REFERENCE` | Bảng LMS WHO 2007 (tháng 120–229) và 5 nhóm phân loại |
| | `bmiForAge(bmi, ageYears, gender)` | `{ z, percentile, medianBmi, category, reference, ageMonths }`; `null` nếu tuổi ngoài 10–19 |
| | `whoAdjustedZScore(value, lms)` | z-score đã hiệu chỉnh ngoài ±3SD (đúng như WHO AnthroPlus) |
| | `normalCdf(z)`, `classifyWhoBmi(z)`, `valueAtZ(lms, z)`, `zFromValue(value, lms)` | Hàm phụ trợ, có thể test độc lập |
| `storage.js` | `initDB()` | Mở/tạo DB `HealthyAppLocalDB`, xin quyền lưu trữ bền vững |
| | `saveRecord(record)` | Thêm 1 bản ghi |
| | `getAllRecords()` | Lấy toàn bộ bản ghi |
| | `deleteRecord(id)` | Xoá 1 bản ghi |
| | `clearAllRecords()` | Xoá toàn bộ bản ghi trên thiết bị |
| | `exportDataToJSON()` | Tải file `suckhoe_backup_YYYY-MM-DD.json` |
| | `importDataFromJSON(file)` | Đọc file JSON và ghi vào DB |

### Định dạng `foods.json`

```json
{
  "id": "pho_bo",
  "name": "Phở bò",
  "group": "tinh_bot",              // tinh_bot | dam | rau_qua | bo_sung
  "role": "main",                   // main (món chính trọn bữa) | side
  "portion": "1 bát (500 ml)",
  "kcal": 430,
  "meals": ["breakfast", "lunch"]   // bữa nào được phép gợi ý
}
```

Thêm món mới = thêm 1 object vào mảng `foods` (giữ `id` duy nhất). Năng lượng tham khảo
Bảng thành phần dinh dưỡng thực phẩm Việt Nam (Viện Dinh dưỡng) và nhãn dinh dưỡng phổ thông,
đã làm tròn — **chỉ dùng cho mục đích học tập, không dùng để chỉ định điều trị**.

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
python -m unittest discover -s tests -v
# hoặc chạy từng file:
python tests/test_nutrition_reference.py -v
python tests/test_food_data.py -v
python -m unittest discover -s tests -p "test_bmi_for_age.py" -v
```

Kết quả mong đợi: `Ran 19 tests ... OK`.

- `test_nutrition_reference.py` đối chiếu **3 case vàng** BMI/BMR/TDEE — nếu sửa công thức trong
  `nutritionEngine.js` mà làm lệch một trong các giá trị bên dưới thì test sẽ báo lỗi.
- `test_food_data.py` kiểm tra `foods.json` (schema, `id` không trùng, ≥ 30 món, mỗi bữa đủ nhóm
  tinh bột / đạm / rau quả), tỷ lệ chia bữa 30/40/30 và việc luôn ghép được khẩu phần nằm trong
  ngân sách calo của từng bữa.
- `test_bmi_for_age.py` so bảng LMS nhúng trong `bmiForAge.js` với **bảng gốc của WHO** (khớp từng
  con số, tháng 120–229) và so z-score với **12 ca do WHO AnthroPlus tính** (dung sai 0.01), kèm
  kiểm tra ranh giới 5 nhóm và bách phân vị.
- `test_version_consistency.py` chặn 2 lỗi hay gặp khi phát hành: (1) `EXPECTED_CACHE` trong
  `index.html` lệch `CACHE_NAME` trong `sw.js` — tức là **quên tăng cache**, người đã cài app sẽ
  chạy mãi bản cũ; (2) một module được `import` trong `index.html` nhưng thiếu trong `ASSETS` của
  Service Worker — app sẽ trắng trang khi mở ngoại tuyến. Test cũng kiểm tra `meta[name="app-version"]`
  đúng định dạng semver và footer thật sự có `#appVersion` / `#swVersion`.

| Case | Ghi chú | BMI | BMR | TDEE | Calo mục tiêu |
| --- | --- | --- | --- | --- | --- |
| Nam 16 tuổi, 70 kg / 170 cm, vận động nhẹ, giảm cân | bị khoá thâm hụt (dưới 18 tuổi) | 24.2 | 1688 | 2321 | **2321** |
| Nữ 20 tuổi, 40 kg / 160 cm, ít vận động, giảm cân | bị khoá thâm hụt (thiếu cân) | 15.6 | 1139 | 1367 | **1367** |
| Nam 25 tuổi, 65 kg / 172 cm, vận động vừa, giảm cân | giảm bình thường 500 kcal | 22.0 | 1605 | 2488 | **1988** |

---

## 7. ⚠️ Quy trình cập nhật code (bắt buộc)

Service Worker trong dự án **cố tình không dùng** `self.skipWaiting()` / sự kiện `activate`
(giữ đúng kiến trúc tối giản của tài liệu). Hệ quả:

> **Mỗi lần sửa `index.html`, `nutritionEngine.js`, `bmiForAge.js`, `recommendations.js`,
> `storage.js`, `foods.json`, `manifest.json` hoặc thay icon → BẮT BUỘC tăng số phiên bản ở
> 3 chỗ đồng bộ.**
>
> ```js
> const CACHE_NAME     = "health-pwa-v5";      // sw.js      → "health-pwa-v6", "health-pwa-v7", ...
> const EXPECTED_CACHE = 'health-pwa-v5';      // index.html → phải trùng CACHE_NAME ở trên
> <meta name="app-version" content="1.2.0">    // index.html → 1.2.1 / 1.3.0 / 2.0.0 (semver)
> <meta name="app-build"   content="2026-11-10"><!-- index.html → ngày phát hành -->
> ```
>
> `python -m unittest discover -s tests` sẽ **báo lỗi ngay** nếu hai tên cache lệch nhau —
> đây là lưới an toàn cho quy tắc này.

Nếu quên bước này, người đã cài app sẽ **tiếp tục chạy bản code cũ** (vì `fetch` trả cache trước).
Sau khi tăng `CACHE_NAME` và deploy, người dùng cần mở app **2 lần** (lần 1 tải Service Worker
mới, lần 2 chạy code mới) hoặc xoá dữ liệu trang trong trình duyệt.

Quy trình chuẩn:

```bash
# 1. Sửa code
# 2. Tăng CACHE_NAME trong sw.js
# 3. Chạy test
python -m unittest discover -s tests -v
# 4. Commit & deploy
git add -A
git commit -m "feat: ..."
git push origin main        # GitHub Pages tự build lại trong ~1 phút
```

### 7.1. Hiển thị phiên bản trong app

Cuối trang có một dòng footer:

> Phiên bản **v1.2.0** (2026-11-10)
> Bộ nhớ đệm health-pwa-v5 — đã là bản mới nhất

- Số phiên bản đọc từ `<meta name="app-version">` ⇒ chỉ cần sửa **một chỗ** trong `index.html`;
  `meta[name="app-build"]` là ngày phát hành.
- Dòng thứ hai đọc **tên cache thật** bằng `caches.keys()` rồi so với `EXPECTED_CACHE`:
  - trùng nhau → *"đã là bản mới nhất"* (kèm danh sách cache cũ nếu còn sót lại);
  - máy còn cache **cũ hơn** (chưa nhận bản mới) → chữ chuyển **màu cảnh báo**:
    *"bản health-pwa-vN sẽ kích hoạt ở lần mở kế tiếp"* — đúng hành vi của Service Worker
    không dùng `skipWaiting` ở mục trên;
  - lần mở đầu tiên (chưa có cache) → *"mở lại ứng dụng một lần để bật chế độ ngoại tuyến"*.
- Nhờ vậy không phải đoán "app đã cập nhật chưa?": mở app là thấy ngay, và sau khi deploy chỉ cần
  mở link kiểm tra footer thay vì xoá dữ liệu trang.

---

## 8. Lịch sử, sao lưu & phục hồi dữ liệu

- **Lịch sử theo dõi** (card ngay dưới phần gợi ý khẩu phần): liệt kê mọi lần đo đã lưu (mới nhất ở
  trên) kèm nhóm BMI theo tuổi, biểu đồ SVG xu hướng BMI (cần ≥ 2 lần đo) và nút xoá từng dòng /
  xoá toàn bộ. Lịch sử được vẽ lại tự động sau mỗi lần tính, sau khi xoá và sau khi phục hồi file.

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
- Xoá dữ liệu: nút **Xoá** trên từng lần đo trong mục *Lịch sử theo dõi*, hoặc **Xoá toàn bộ lịch
  sử** (bấm 2 lần để xác nhận, tránh nhầm) — đáp ứng quyền xoá dữ liệu của chủ thể dữ liệu. Cách
  khác: xoá dữ liệu trang trong trình duyệt (Settings → Site data) hoặc gỡ app khỏi màn hình chính.

---

## 10. Triển khai (GitHub Pages)

Repo đã bật GitHub Pages, nguồn là nhánh `main`:

1. Push lên `main` → GitHub Pages tự build (khoảng 1 phút).
2. Truy cập <https://thinhbnt.github.io/suc-khoe-hoc-duong/>.
3. Kiểm tra **footer** ở cuối trang: phải hiện đúng số phiên bản vừa phát hành và
   *"Bộ nhớ đệm health-pwa-vN — đã là bản mới nhất"*. Nếu vẫn thấy số cũ, CDN của GitHub Pages
   đang giữ bản cache (thường vài phút) — chờ rồi tải lại.
4. Không cần mua server hay tên miền; HTTPS có sẵn (bắt buộc để cài PWA).
   Có thể thay bằng Cloudflare Pages / Vercel / Firebase Hosting nếu muốn.

---

## 11. Miễn trừ y khoa

> Kết quả chỉ mang tính tham khảo dành cho người khỏe mạnh. Người có bệnh nền, rối loạn chuyển hóa
> hoặc đang điều trị y khoa cần tham vấn ý kiến chuyên gia dinh dưỡng.

Ứng dụng không thay thế chẩn đoán hay chỉ định của bác sĩ, và chủ động không thu thập thông tin
bệnh lý để tránh tư vấn y khoa ngoài phạm vi an toàn.

Gợi ý khẩu phần chỉ là **ví dụ minh hoạ** dựa trên 35 món Việt phổ thông trong `foods.json`
(năng lượng làm tròn, không tính đến dị ứng, bệnh nền, tôn giáo hay điều kiện kinh tế).
Khuyến cáo vận động trích theo WHO 2020 và cần được điều chỉnh bởi giáo viên thể chất /
nhân viên y tế nhà trường khi áp dụng thực tế.

Phân loại **BMI theo tuổi** (WHO 2007) là công cụ **sàng lọc cộng đồng**, không phải chẩn đoán:
học sinh có z-score dưới −2 hoặc trên +2 SD nên được nhân viên y tế nhà trường đánh giá thêm
(không tự ý ăn kiêng theo app).



