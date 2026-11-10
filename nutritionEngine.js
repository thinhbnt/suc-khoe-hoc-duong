// nutritionEngine.js
export const ACTIVITY_MULTIPLIERS = {
  sedentary: 1.2,       // Ít/không vận động
  light: 1.375,         // Vận động nhẹ (1-3 ngày/tuần)
  moderate: 1.55,       // Vận động vừa (3-5 ngày/tuần)
  very_active: 1.725    // Vận động nặng (6-7 ngày/tuần)
};
export const GOAL_ADJUSTMENTS = {
  lose: -500,    // Thâm hụt 500 kcal/ngày (~0.5 kg/tuần)
  maintain: 0,
  gain: 500      // Thặng dư 500 kcal/ngày (~0.5 kg/tuần)
};
export function validateInput({ weight, height, age, gender, activityLevel, goal }) {
  if (weight < 20 || weight > 300) throw new Error("Cân nặng không hợp lý (20 - 300 kg).");
  if (height < 100 || height > 250) throw new Error("Chiều cao không hợp lý (100 - 250 cm).");
  if (age < 10 || age > 100) throw new Error("Tuổi không hợp lý (10 - 100 tuổi).");
  if (!['male', 'female'].includes(gender)) throw new Error("Giới tính không hợp lệ.");
  if (!ACTIVITY_MULTIPLIERS[activityLevel]) throw new Error("Mức độ vận động không hợp lệ.");
  if (!GOAL_ADJUSTMENTS.hasOwnProperty(goal)) throw new Error("Mục tiêu không hợp lệ.");
}
export function calculateMetrics({ weight, height, age, gender, activityLevel, goal }) {
  validateInput({ weight, height, age, gender, activityLevel, goal });
  // 1. Chỉ số BMI (WHO Châu Á - Thái Bình Dương)
  const heightM = height / 100;
  const bmi = +(weight / (heightM * heightM)).toFixed(1);

  let bmiCategory = "";
  if (bmi < 18.5) bmiCategory = "Thiếu cân";
  else if (bmi < 23.0) bmiCategory = "Bình thường";
  else if (bmi < 25.0) bmiCategory = "Tiền béo phì (Thừa cân)";
  else if (bmi < 30.0) bmiCategory = "Béo phì độ I";
  else bmiCategory = "Béo phì độ II";
  // 2. BMR (Mifflin-St Jeor)
  // Nam: 10W + 6.25H - 5A + 5 | Nữ: 10W + 6.25H - 5A - 161
  const s = gender === 'male' ? 5 : -161;
  const bmr = Math.round(10 * weight + 6.25 * height - 5 * age + s);
  // 3. TDEE
  const tdee = Math.round(bmr * ACTIVITY_MULTIPLIERS[activityLevel]);
  // 4. Calo mục tiêu & Rào chắn an toàn (Safety Guardrails)
  let targetCalories = tdee + GOAL_ADJUSTMENTS[goal];
  const warnings = [];
  if (age < 18) {
    warnings.push("Học sinh dưới 18 tuổi đang trong giai đoạn phát triển thể chất; không nên ăn kiêng thâm hụt calo nếu không có chỉ định y khoa.");
    if (goal === 'lose') {
      targetCalories = tdee; // Chặn thâm hụt calo ở lứa tuổi phát triển
    }
  }
  if (bmi < 18.5 && goal === 'lose') {
    warnings.push("Thể trạng hiện tại đang thiếu cân; chế độ giảm cân bị khóa để đảm bảo an toàn.");
    targetCalories = tdee;
  }
  // Sàn calo tối thiểu sinh học
  const minFloor = gender === 'male' ? 1500 : 1200;
  if (targetCalories < minFloor) {
    targetCalories = minFloor;
    warnings.push(`Mức calo đã được điều chỉnh về ngưỡng an toàn tối thiểu (${minFloor} kcal/ngày).`);
  }
  return {
    bmi,
    bmiCategory,
    bmr,
    tdee,
    targetCalories,
    warnings,
    calculatedAt: new Date().toISOString()
  };
}

// Tỷ lệ phân bổ calo theo bữa: Sáng 30% - Trưa 40% - Tối 30%
export const MEAL_SPLIT = {
  breakfast: 0.3,
  lunch: 0.4,
  dinner: 0.3
};

export const MEAL_LABELS = {
  breakfast: "Bữa sáng",
  lunch: "Bữa trưa",
  dinner: "Bữa tối"
};

// Chia calo mục tiêu cho 3 bữa theo tỷ lệ 30/40/30.
// Bữa tối nhận phần còn lại để tổng 3 bữa luôn bằng đúng calo mục tiêu
// (tránh lệch 1-2 kcal do làm tròn từng bữa).
export function splitMeals(targetCalories) {
  const breakfast = Math.round(targetCalories * MEAL_SPLIT.breakfast);
  const lunch = Math.round(targetCalories * MEAL_SPLIT.lunch);
  return {
    breakfast,
    lunch,
    dinner: targetCalories - breakfast - lunch
  };
}
