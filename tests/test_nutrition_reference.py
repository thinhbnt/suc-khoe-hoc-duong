# test_nutrition_reference.py
import unittest

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725
}

GOAL_ADJUSTMENTS = {
    "lose": -500,
    "maintain": 0,
    "gain": 500
}


def calculate_metrics_py(weight: float, height: float, age: int, gender: str, activity_level: str, goal: str):
    # 1. BMI
    height_m = height / 100.0
    bmi = round(weight / (height_m ** 2), 1)

    if bmi < 18.5:
        bmi_cat = "Thiếu cân"
    elif bmi < 23.0:
        bmi_cat = "Bình thường"
    elif bmi < 25.0:
        bmi_cat = "Tiền béo phì (Thừa cân)"
    elif bmi < 30.0:
        bmi_cat = "Béo phì độ I"
    else:
        bmi_cat = "Béo phì độ II"

    # 2. BMR (Mifflin-St Jeor)
    s = 5 if gender == "male" else -161
    bmr = round(10 * weight + 6.25 * height - 5 * age + s)

    # 3. TDEE
    tdee = round(bmr * ACTIVITY_MULTIPLIERS[activity_level])

    # 4. Target & Guards
    target = tdee + GOAL_ADJUSTMENTS[goal]
    warnings = []

    if age < 18:
        warnings.append("Học sinh dưới 18 tuổi")
        if goal == "lose":
            target = tdee

    if bmi < 18.5 and goal == "lose":
        warnings.append("Thiếu cân")
        target = tdee

    min_floor = 1500 if gender == "male" else 1200
    if target < min_floor:
        target = min_floor

    return {
        "bmi": bmi,
        "bmiCategory": bmi_cat,
        "bmr": bmr,
        "tdee": tdee,
        "targetCalories": target
    }


class TestNutritionEngine(unittest.TestCase):
    def test_case_student_under_18(self):
        # Case 1: Nam học sinh 16 tuổi, thừa cân, chọn giảm cân -> Chặn thâm hụt
        res = calculate_metrics_py(weight=70, height=170, age=16, gender="male", activity_level="light", goal="lose")
        self.assertEqual(res["bmi"], 24.2)
        self.assertEqual(res["bmiCategory"], "Tiền béo phì (Thừa cân)")
        self.assertEqual(res["bmr"], 1688)
        self.assertEqual(res["tdee"], 2321)
        self.assertEqual(res["targetCalories"], 2321)  # Bị khóa không cho thâm hụt

    def test_case_underweight_lock(self):
        # Case 2: Nữ 20 tuổi thiếu cân muốn giảm cân -> Khóa giảm cân, chặn sàn tối thiểu 1200
        res = calculate_metrics_py(weight=40, height=160, age=20, gender="female", activity_level="sedentary", goal="lose")
        self.assertEqual(res["bmi"], 15.6)
        self.assertEqual(res["bmiCategory"], "Thiếu cân")
        self.assertEqual(res["bmr"], 1139)
        self.assertEqual(res["tdee"], 1367)
        self.assertEqual(res["targetCalories"], 1367)  # Giữ nguyên TDEE

    def test_case_adult_cut(self):
        # Case 3: Nam 25 tuổi, bình thường, giảm cân -> Giảm 500 kcal
        res = calculate_metrics_py(weight=65, height=172, age=25, gender="male", activity_level="moderate", goal="lose")
        self.assertEqual(res["bmi"], 22.0)
        self.assertEqual(res["bmiCategory"], "Bình thường")
        self.assertEqual(res["bmr"], 1605)
        self.assertEqual(res["tdee"], 2488)
        self.assertEqual(res["targetCalories"], 1988)


if __name__ == "__main__":
    unittest.main()
