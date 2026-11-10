"""Kiểm thử chức năng đổi món trong khẩu phần (tìm kiếm không dấu).

Phần tìm kiếm chạy bằng JavaScript nên hành vi được kiểm tra ở e2e.js (trình duyệt
thật). File này giữ những "hợp đồng" tĩnh dễ vỡ khi sửa code:

- recommendations.js phải export đủ hàm mà giao diện dùng;
- nhãn nhóm món (GROUP_LABELS) phải trùng meta.groups trong foods.json;
- index.html phải thật sự nối ô tìm kiếm vào sự kiện và cộng lại calo;
- mỗi bữa phải có đủ món để ô tìm kiếm có lựa chọn thay thế.
"""
import io
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")
RECO_PATH = os.path.join(ROOT, "recommendations.js")
FOODS_PATH = os.path.join(ROOT, "foods.json")

MEALS = ("breakfast", "lunch", "dinner")
EXPORTED = ("normalizeForSearch", "searchFoods", "summarizeMeal", "GROUP_LABELS")


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def group_labels(js):
    """Đọc object GROUP_LABELS trong recommendations.js thành dict."""
    block = re.search(r"export\s+const\s+GROUP_LABELS\s*=\s*\{(.*?)\};", js, re.S)
    if not block:
        return {}
    return dict(re.findall(r"(\w+)\s*:\s*\"([^\"]*)\"", block.group(1)))


class TestSearchContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = read(INDEX_PATH)
        cls.rec = read(RECO_PATH)
        with io.open(FOODS_PATH, encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_01_module_export_du_ham(self):
        for name in EXPORTED:
            self.assertRegex(
                self.rec,
                r"export\s+(const|function)\s+%s\b" % name,
                "recommendations.js chưa export %s" % name,
            )

    def test_02_nhan_nhom_mon_khop_foods_json(self):
        labels = group_labels(self.rec)
        self.assertTrue(labels, "Không đọc được GROUP_LABELS trong recommendations.js")
        self.assertEqual(
            labels,
            self.data["meta"]["groups"],
            "GROUP_LABELS trong recommendations.js lệch meta.groups trong foods.json",
        )

    def test_03_tim_khong_dau_co_xu_ly_d(self):
        # "đ/Đ" không tách được bằng NFD nên phải thay riêng, nếu thiếu thì
        # gõ "dau" sẽ không tìm ra "Đậu phụ".
        self.assertIn('normalize("NFD")', self.rec)
        self.assertIn("[\\u0300-\\u036f]", self.rec)
        self.assertIn('.replace(/đ/g, "d")', self.rec)
        self.assertIn('.replace(/Đ/g, "d")', self.rec)

    def test_04_index_html_noi_dung_o_tim_kiem(self):
        self.assertIn("searchFoods", self.html)
        self.assertIn("summarizeMeal", self.html)
        self.assertIn("class=\"btn-swap\"", self.html)
        self.assertIn('class="swap-input"', self.html)
        self.assertIn("renderSwapResults(", self.html)
        self.assertIn("applySwap(", self.html)
        # tổng calo cả ngày phải được vẽ lại kèm data-total (e2e.js kiểm tra)
        self.assertIn('id="planTotal"', self.html)
        self.assertIn('data-total="${total}"', self.html)

    def test_05_moi_bua_du_mon_de_thay_the(self):
        for meal in MEALS:
            pool = [f for f in self.data["foods"] if meal in f["meals"]]
            self.assertGreaterEqual(
                len(pool), 5, "Bữa %s chỉ có %d món — ô tìm kiếm quá ít lựa chọn" % (meal, len(pool))
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
