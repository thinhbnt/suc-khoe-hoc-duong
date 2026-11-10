# test_food_data.py
# Kiểm tra dữ liệu món ăn (foods.json), tỷ lệ chia bữa 30/40/30 và khả năng
# gợi ý được khẩu phần trong ngân sách calo của từng bữa.
import json
import math
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOODS_PATH = os.path.join(BASE_DIR, "foods.json")

GROUPS = {"tinh_bot", "dam", "rau_qua", "bo_sung"}
CORE_GROUPS = ("tinh_bot", "dam", "rau_qua")
MEALS = ("breakfast", "lunch", "dinner")
MEAL_SPLIT = {"breakfast": 0.3, "lunch": 0.4, "dinner": 0.3}


def js_round(x):
    """Mô phỏng Math.round() của JavaScript (0.5 làm tròn lên)."""
    return math.floor(x + 0.5)


def split_meals(target_calories):
    """Bản Python của splitMeals() trong nutritionEngine.js."""
    breakfast = js_round(target_calories * MEAL_SPLIT["breakfast"])
    lunch = js_round(target_calories * MEAL_SPLIT["lunch"])
    return {"breakfast": breakfast, "lunch": lunch, "dinner": target_calories - breakfast - lunch}


class FoodDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FOODS_PATH, encoding="utf-8") as fh:
            cls.data = json.load(fh)
        cls.foods = cls.data["foods"]

    def test_01_schema_hop_le(self):
        self.assertGreaterEqual(len(self.foods), 30, "Cần tối thiểu 30 món ăn mẫu")
        ids = [f["id"] for f in self.foods]
        self.assertEqual(len(ids), len(set(ids)), "id món ăn bị trùng")
        required = {"id", "name", "group", "portion", "kcal", "meals"}
        for food in self.foods:
            missing = required - set(food.keys())
            self.assertFalse(missing, f"{food.get('id')} thiếu trường {missing}")
            self.assertIn(food["group"], GROUPS, food["id"])
            self.assertIn(food.get("role", "side"), {"main", "side"}, food["id"])
            self.assertIsInstance(food["kcal"], int, food["id"])
            self.assertTrue(10 <= food["kcal"] <= 900, food["id"])
            self.assertTrue(food["portion"].strip(), food["id"])
            self.assertTrue(food["meals"], food["id"])
            self.assertTrue(set(food["meals"]) <= set(MEALS), food["id"])

    def test_02_moi_bua_du_nhom_mon(self):
        for meal in MEALS:
            for group in CORE_GROUPS:
                pool = [f for f in self.foods if meal in f["meals"] and f["group"] == group]
                self.assertTrue(pool, f"{meal} thiếu món thuộc nhóm {group}")

    def test_03_ty_le_chia_bua_30_40_30(self):
        expected = {"breakfast": 696, "lunch": 928, "dinner": 697}
        self.assertEqual(split_meals(2321), expected)

        # Bữa sáng và bữa tối luôn bằng nhau về tỷ lệ (30%), bữa trưa 40%
        for target in (1200, 1500, 1988, 2321, 2600, 3000):
            parts = split_meals(target)
            self.assertEqual(sum(parts.values()), target, "Tổng 3 bữa phải bằng calo mục tiêu")
            self.assertAlmostEqual(parts["breakfast"] / target, 0.3, delta=0.002)
            self.assertAlmostEqual(parts["lunch"] / target, 0.4, delta=0.002)
            self.assertAlmostEqual(parts["dinner"] / target, 0.3, delta=0.002)

    def test_04_goi_y_khau_phan_nam_trong_ngan_sach(self):
        """Mỗi bữa phải gợi ý được ít nhất: 1 món nền + 1 món rau/quả <= ngân sách."""
        for target in (1200, 1500, 1988, 2321, 3000):
            budgets = split_meals(target)
            for meal in MEALS:
                budget = budgets[meal]
                pool = [f for f in self.foods if meal in f["meals"]]
                bases = [f for f in pool if f.get("role") == "main" and f["kcal"] <= budget]
                bases += [f for f in pool if f.get("role", "side") == "side" and f["group"] in ("tinh_bot", "dam")]
                veggies = [f for f in pool if f["group"] == "rau_qua"]

                self.assertTrue(bases, f"{meal}: không có món nền nào vừa ngân sách {budget} kcal")
                self.assertTrue(veggies, f"{meal}: không có món rau/quả nào")

                comfortable = [
                    (b, v) for b in bases for v in veggies if b["kcal"] + v["kcal"] <= budget
                ]
                self.assertTrue(
                    comfortable,
                    f"{meal}: không ghép được món nền + rau/quả trong {budget} kcal"
                )

    def test_05_meta_co_nguon_du_lieu(self):
        meta = self.data["meta"]
        self.assertTrue(meta["source"].strip(), "Thiếu nguồn dữ liệu tham khảo")
        self.assertIn("dinh dưỡng", meta["source"].lower())
        self.assertTrue(meta["note"].strip())
        self.assertEqual(set(meta["groups"].keys()), GROUPS)
        self.assertEqual(set(meta["meals"].keys()), set(MEALS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
