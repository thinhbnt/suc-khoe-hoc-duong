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
