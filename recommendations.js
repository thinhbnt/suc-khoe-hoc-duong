// recommendations.js
// Tầng khuyến cáo: gợi ý khẩu phần theo ngân sách calo từng bữa (30/40/30)
// và khuyến cáo vận động thể lực theo nhóm tuổi (tham khảo WHO 2020).
// Toàn bộ là hàm thuần (pure) để dễ kiểm thử, không phụ thuộc DOM.

/**
 * Tải dữ liệu món ăn từ foods.json (cache lại sau lần đầu).
 */
let foodsCache = null;
export async function loadFoods() {
  if (foodsCache) return foodsCache;
  const res = await fetch("./foods.json");
  if (!res.ok) throw new Error("Không tải được dữ liệu món ăn (foods.json).");
  const data = await res.json();
  if (!data || !Array.isArray(data.foods)) {
    throw new Error("Dữ liệu món ăn không đúng định dạng.");
  }
  foodsCache = data;
  return data;
}

// Sắp xếp: kcal giảm dần, cùng kcal thì theo id để kết quả luôn ổn định.
function byKcalDesc(a, b) {
  return b.kcal - a.kcal || a.id.localeCompare(b.id);
}

// Nhãn nhóm món ăn dùng cho ô tìm kiếm (phải khớp meta.groups trong foods.json —
// tests/test_food_search.py kiểm tra để hai nơi không lệch nhau).
export const GROUP_LABELS = {
  tinh_bot: "Tinh bột",
  dam: "Đạm (thịt, cá, trứng, đậu)",
  rau_qua: "Rau & trái cây",
  bo_sung: "Bổ sung (sữa, hạt, chất béo)"
};

/**
 * Gợi ý khẩu phần cho 1 bữa trong phạm vi ngân sách calo của bữa đó.
 *
 * Thứ tự chọn (giải thích được khi thuyết trình):
 *  1. Món chính trọn bữa (phở, bánh mì, xôi, bánh cuốn, bún chả) nếu vừa ngân sách;
 *     nếu không có thì 1 món tinh bột + 1 món đạm.
 *  2. Thêm tối đa 2 món rau / trái cây.
 *  3. Thêm tối đa 2 món bổ sung (sữa, hạt, chất béo) khi còn ≥ 60 kcal.
 *  4. Nếu vẫn còn dư ≥ 150 kcal, thêm 1 khẩu phần đạm (hoặc tinh bột).
 * Phần calo còn dư được trả về trong `remainingKcal` để giao diện nhắc người dùng.
 */
export function buildMealPlan(mealKey, budgetKcal, foods) {
  const used = new Set();
  const items = [];
  let rest = budgetKcal;

  const pool = foods.filter(
    (f) => Array.isArray(f.meals) && f.meals.includes(mealKey)
  );
  const take = (group, maxKcal) => {
    if (rest <= 0) return null;
    const limit = Math.min(maxKcal, rest);
    const found = pool
      .filter((f) => f.group === group && !used.has(f.id) && f.kcal <= limit)
      .sort(byKcalDesc)[0];
    if (!found) return null;
    used.add(found.id);
    items.push(found);
    rest -= found.kcal;
    return found;
  };

  // 1. Món chính trọn bữa
  const main = pool
    .filter((f) => f.role === "main" && f.kcal <= budgetKcal)
    .sort(byKcalDesc)[0];
  if (main && main.kcal >= budgetKcal * 0.55) {
    used.add(main.id);
    items.push(main);
    rest -= main.kcal;
  } else {
    const carb = take("tinh_bot", budgetKcal); // 1 món tinh bột
    if (carb) {
      // 1 món đạm: ưu tiên chừa ~60 kcal cho rau; nếu không món nào vừa thì nới ngưỡng
      if (!take("dam", rest - 60)) take("dam", rest - 20);
    } else {
      take("dam", rest); // bữa quá nhỏ, không có món tinh bột nào vừa ngân sách
    }
  }

  // 2. Rau / trái cây (tối đa 2 khẩu phần)
  take("rau_qua", rest);
  take("rau_qua", rest);

  // 3. Bổ sung (tối đa 2 khẩu phần) khi còn đủ chỗ
  for (let i = 0; i < 2 && rest >= 60; i++) {
    if (!take("bo_sung", rest)) break;
  }

  // 4. Nếu vẫn còn dư nhiều (>= 150 kcal), thêm 1 khẩu phần đạm hoặc tinh bột
  if (rest >= 150 && !take("dam", rest)) {
    take("tinh_bot", rest);
  }

  return {
    meal: mealKey,
    budgetKcal,
    items,
    totalKcal: budgetKcal - rest,
    remainingKcal: rest
  };
}

/**
 * Cộng lại calo của một bữa sau khi người dùng đổi món.
 * Dùng chung cho giao diện: tổng bữa và phần calo còn dư luôn được tính lại
 * từ danh sách món hiện tại, không lưu sẵn con số nào.
 */
export function summarizeMeal(items, budgetKcal) {
  const list = Array.isArray(items) ? items : [];
  const totalKcal = list.reduce((sum, item) => sum + (Number(item && item.kcal) || 0), 0);
  return {
    totalKcal,
    remainingKcal: (Number(budgetKcal) || 0) - totalKcal
  };
}

/**
 * Bỏ dấu tiếng Việt để tìm kiếm không dấu:
 *   "Phở bò" -> "pho bo", "Đậu phụ luộc" -> "dau phu luoc".
 * Chữ "đ/Đ" không tách được bằng NFD nên phải thay riêng.
 */
export function normalizeForSearch(text) {
  return String(text == null ? "" : text)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "d")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Tìm món ăn để thay thế: không phân biệt dấu, không phân biệt hoa/thường.
 * - Chỉ lấy món dùng được cho bữa đang xét (trường "meals" trong foods.json).
 * - Ưu tiên: trùng khít tên > tên bắt đầu bằng từ khoá > tên chứa từ khoá >
 *   khớp rời từng từ > từ khoá bắt đầu bằng tên nhóm món ("rau", "dam", "tinh"...);
 *   cùng mức ưu tiên thì kcal giảm dần.
 * - Từ khoá rỗng trả về toàn bộ món của bữa (để người dùng xem danh sách).
 */
export function searchFoods(query, foods, mealKey) {
  const list = Array.isArray(foods) ? foods : [];
  const pool = mealKey
    ? list.filter((f) => Array.isArray(f.meals) && f.meals.includes(mealKey))
    : list.slice();
  const q = normalizeForSearch(query);
  if (!q) return pool.slice().sort(byKcalDesc);

  const words = q.split(" ").filter(Boolean);
  const scored = [];
  for (const food of pool) {
    const name = normalizeForSearch(food.name);
    const group = normalizeForSearch(GROUP_LABELS[food.group] || food.group);
    let score;
    if (name === q) score = 0;
    else if (name.startsWith(q)) score = 1;
    else if (name.includes(q)) score = 2;
    else if (words.length > 1 && words.every((w) => name.includes(w))) score = 3;
    // Chỉ khớp nhóm khi từ khoá BẮT ĐẦU bằng tên nhóm ("dau" sẽ không kéo theo
    // cả nhóm "Đạm (thịt, cá, trứng, đậu)").
    else if (group.startsWith(q)) score = 4;
    else continue;
    scored.push({ food, score });
  }
  scored.sort((a, b) => a.score - b.score || byKcalDesc(a.food, b.food));
  return scored.map((entry) => entry.food);
}

/**
 * Khuyến cáo vận động thể lực theo nhóm tuổi (tham khảo WHO 2020).
 * Trả về null nếu tuổi ngoài phạm vi hỗ trợ (10 - 100 tuổi).
 */
export function getActivityAdvice(age) {
  if (typeof age !== "number" || Number.isNaN(age) || age < 10 || age > 100) {
    return null;
  }

  if (age < 18) {
    return {
      group: "5 - 17 tuổi",
      headline: "Vận động thể lực trung bình - mạnh ít nhất 60 phút mỗi ngày",
      details: [
        "Chủ yếu là vận động nhịp tim: đi bộ nhanh, đạp xe, bơi lội, chạy, chơi bóng, nhảy dây.",
        "Ít nhất 3 ngày/tuần có hoạt động mạnh giúp tăng cường cơ và xương.",
        "Hạn chế thời gian ngồi giải trí trước màn hình; sau 45 - 60 phút học bài nên đứng lên vận động nhẹ."
      ],
      source: "WHO Guidelines on physical activity and sedentary behaviour (2020)"
    };
  }

  if (age < 65) {
    return {
      group: "18 - 64 tuổi",
      headline: "150 - 300 phút/tuần vận động trung bình, hoặc 75 - 150 phút/tuần vận động mạnh",
      details: [
        "Có thể chia nhỏ: 30 phút x 5 ngày/tuần đi bộ nhanh hoặc đạp xe.",
        "Tập sức mạnh cho các nhóm cơ chính ít nhất 2 ngày/tuần.",
        "Hạn chế thời gian tĩnh tại kéo dài; ngồi lâu nên đứng lên vận động nhẹ."
      ],
      source: "WHO Guidelines on physical activity and sedentary behaviour (2020)"
    };
  }

  return {
    group: "65 tuổi trở lên",
    headline: "150 - 300 phút/tuần vận động trung bình, hoặc 75 - 150 phút/tuần vận động mạnh",
    details: [
      "Thêm bài tập thăng bằng ít nhất 3 ngày/tuần để giảm nguy cơ té ngã.",
      "Tập sức mạnh cho các nhóm cơ chính ít nhất 2 ngày/tuần.",
      "Chọn hình thức phù hợp thể trạng: đi bộ, dưỡng sinh, bơi, đạp xe tại chỗ."
    ],
    source: "WHO Guidelines on physical activity and sedentary behaviour (2020)"
  };
}
