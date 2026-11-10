"""Kiểm thử bmiForAge.js đối chiếu với dữ liệu gốc và kết quả mẫu của WHO.

Fixture:
  tests/fixtures/bfawho2007.txt          - bảng LMS gốc (repo WHO anthroplus)
  tests/fixtures/who2007_zbmi_sample.csv - 12 ca (bmi, tuổi tháng, z) do WHO tính
"""
import csv
import io
import math
import os
import re
import unittest

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bmiForAge.js")


def load_who_reference():
    """Đọc bảng LMS gốc của WHO: {(sex, month): (L, M, S)}."""
    table = {}
    with io.open(os.path.join(FIXTURES, "bfawho2007.txt"), encoding="utf-8-sig") as fh:
        next(fh)  # bỏ header: sex age l m s
        for line in fh:
            parts = line.split()
            if len(parts) < 5:
                continue
            table[(int(parts[0]), int(parts[1]))] = (float(parts[2]), float(parts[3]), float(parts[4]))
    return table


def load_js_table():
    """Đọc bảng LMS nhúng trong bmiForAge.js: {sex: {month: (L, M, S)}}."""
    with io.open(MODULE_PATH, encoding="utf-8") as fh:
        src = fh.read()
    male_block, female_block = src.split("// 2 = nữ", 1)
    row_re = re.compile(r"\[\s*(-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(\d+\.\d+)\s*\],\s*//\s*(\d+)\s*tháng")
    out = {}
    for sex, block in ((1, male_block), (2, female_block)):
        out[sex] = {int(m.group(4)): (float(m.group(1)), float(m.group(2)), float(m.group(3)))
                    for m in row_re.finditer(block)}
    return out


def lms_at(table, sex, age_months):
    """Nội suy tuyến tính giữa 2 tháng tuổi - giống hệt lmsAt() trong JS."""
    low = int(math.floor(age_months))
    frac = age_months - low
    a = table[sex][low]
    if frac == 0:
        return a
    b = table[sex][low + 1]
    return tuple(a[i] + frac * (b[i] - a[i]) for i in range(3))


def value_at_z(lms, z):
    l, m, s = lms
    if abs(l) < 1e-9:
        return m * math.exp(s * z)
    return m * (1 + l * s * z) ** (1 / l)


def z_direct(value, lms):
    l, m, s = lms
    if abs(l) < 1e-9:
        return math.log(value / m) / s
    return ((value / m) ** l - 1) / (l * s)


def z_adjusted(value, lms):
    """Giống whoAdjustedZScore(): ngoài ±3SD dùng nội suy tuyến tính SD2-SD3."""
    z = z_direct(value, lms)
    if z > 3:
        sd3, sd2 = value_at_z(lms, 3), value_at_z(lms, 2)
        return 3 + (value - sd3) / (sd3 - sd2)
    if z < -3:
        sd3, sd2 = value_at_z(lms, -3), value_at_z(lms, -2)
        return -3 + (value - sd3) / (sd2 - sd3)
    return z


def normal_cdf(z):
    """Φ(z) xấp xỉ Abramowitz & Stegun 7.1.26 - giống normalCdf() trong JS."""
    sign = -1 if z < 0 else 1
    x = abs(z) / math.sqrt(2)
    t = 1 / (1 + 0.3275911 * x)
    poly = ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t
    return 0.5 * (1 + sign * (1 - poly * math.exp(-x * x)))


def classify(z):
    if z < -3:
        return "Gầy nặng"
    if z < -2:
        return "Gầy"
    if z <= 1:
        return "Bình thường"
    if z <= 2:
        return "Thừa cân"
    return "Béo phì"


class TestBmiForAge(unittest.TestCase):
    def setUp(self):
        self.who = load_who_reference()
        self.js = load_js_table()

    def test_01_bang_lms_nhung_khop_du_lieu_who(self):
        """Bảng LMS trong JS phải trùng khít bảng gốc của WHO (tháng 120-229)."""
        for sex in (1, 2):
            self.assertEqual(len(self.js[sex]), 110, "sex %d phải có 110 dòng (120-229)" % sex)
            for month in range(120, 230):
                self.assertIn(month, self.js[sex])
                self.assertEqual(self.js[sex][month], self.who[(sex, month)],
                                 "Lệch dữ liệu WHO tại sex %d, tháng %d" % (sex, month))

    def test_02_z_score_khop_ket_qua_mau_cua_who(self):
        """z-score tính từ bảng nhúng phải khớp 12 ca do WHO AnthroPlus tính."""
        with io.open(os.path.join(FIXTURES, "who2007_zbmi_sample.csv"), encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 12)
        self.assertTrue(any(abs(float(r["z_who"])) > 3 for r in rows),
                        "Bộ mẫu phải có ca |z| > 3 để kiểm tra nhánh z hiệu chỉnh")
        for row in rows:
            sex = int(row["sex"])
            age_months = float(row["age_months"])
            bmi = float(row["bmi"])
            z = round(z_adjusted(bmi, lms_at(self.js, sex, age_months)), 2)
            self.assertAlmostEqual(z, float(row["z_who"]), delta=0.011,
                                   msg="sex=%s tháng=%s BMI=%s" % (sex, age_months, bmi))

    def test_03_phan_loai_5_nhom_theo_sd(self):
        cases = {
            -3.5: "Gầy nặng", -3.0: "Gầy", -2.5: "Gầy", -2.0: "Bình thường",
            0.0: "Bình thường", 1.0: "Bình thường", 1.01: "Thừa cân", 2.0: "Thừa cân",
            2.01: "Béo phì", 4.21: "Béo phì",
        }
        for z in sorted(cases):
            self.assertEqual(classify(z), cases[z], "z=%s" % z)

    def test_04_bach_phan_vi_tu_z(self):
        self.assertAlmostEqual(normal_cdf(0), 0.5, places=6)
        self.assertAlmostEqual(normal_cdf(1.6449) * 100, 95, delta=0.02)
        self.assertAlmostEqual(normal_cdf(-1.96) * 100, 2.5, delta=0.02)
        self.assertAlmostEqual(normal_cdf(2) * 100, 97.72, delta=0.02)
        self.assertLess(normal_cdf(-1), normal_cdf(0))

    def test_05_gioi_han_tuoi_va_tham_so_module(self):
        """Module chỉ phủ 10-19 tuổi; hằng số phải khai báo đúng."""
        with io.open(MODULE_PATH, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("export const WHO_BMI_MIN_AGE = 10;", src)
        self.assertIn("export const WHO_BMI_MAX_AGE = 19;", src)
        self.assertIn("WHO 2007", src)
        for sex in (1, 2):
            self.assertEqual(sorted(self.js[sex]), list(range(120, 230)),
                             "sex %d phải liên tục 120-229" % sex)


if __name__ == "__main__":
    unittest.main(verbosity=2)

