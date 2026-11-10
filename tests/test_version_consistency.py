"""Kiểm thử việc hiển thị phiên bản và sự đồng bộ giữa index.html với sw.js.

Mục đích: chặn lỗi "quên tăng CACHE_NAME" (quy tắc bắt buộc ở README §7) và
bảo đảm mọi module ES được import trong index.html đều có trong danh sách ASSETS
của Service Worker (nếu thiếu, app sẽ trắng trang khi chạy offline).
"""
import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")
SW_PATH = os.path.join(ROOT, "sw.js")

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
BUILD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CACHE_RE = re.compile(r"^health-pwa-v(\d+)$")


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def meta_content(html, name):
    match = re.search(r'<meta\s+name="%s"\s+content="([^"]*)"' % re.escape(name), html)
    return match.group(1) if match else None


def expected_cache(html):
    match = re.search(r"const\s+EXPECTED_CACHE\s*=\s*['\"]([^'\"]+)['\"]", html)
    return match.group(1) if match else None


def sw_cache_name(sw):
    match = re.search(r"const\s+CACHE_NAME\s*=\s*['\"]([^'\"]+)['\"]", sw)
    return match.group(1) if match else None


def sw_assets(sw):
    block = re.search(r"const\s+ASSETS\s*=\s*\[(.*?)\]", sw, re.S)
    if not block:
        return []
    return [os.path.basename(p) for p in re.findall(r"['\"]\./([^'\"]+)['\"]", block.group(1))]


class TestVersionDisplay(unittest.TestCase):
    """Số phiên bản hiển thị trong app phải đọc được và đúng định dạng."""

    @classmethod
    def setUpClass(cls):
        cls.html = read(INDEX_PATH)
        cls.sw = read(SW_PATH)

    def test_app_version_is_semver(self):
        version = meta_content(self.html, "app-version")
        self.assertIsNotNone(version, "Thiếu <meta name=\"app-version\"> trong index.html")
        self.assertRegex(version, SEMVER_RE)

    def test_app_build_is_iso_date(self):
        build = meta_content(self.html, "app-build")
        self.assertIsNotNone(build, "Thiếu <meta name=\"app-build\"> trong index.html")
        self.assertRegex(build, BUILD_RE)

    def test_footer_shows_version_and_cache(self):
        self.assertIn('id="appVersion"', self.html)
        self.assertIn('id="appBuild"', self.html)
        self.assertIn('id="swVersion"', self.html)
        self.assertIn("class=\"app-footer\"", self.html)
        # script phải thực sự vẽ số phiên bản và đọc Cache Storage
        self.assertIn("metaContent('app-version')", self.html)
        self.assertIn("caches.keys()", self.html)
        self.assertIn("renderVersion();", self.html)


class TestCacheSync(unittest.TestCase):
    """EXPECTED_CACHE (index.html) và CACHE_NAME (sw.js) không được lệch nhau."""

    @classmethod
    def setUpClass(cls):
        cls.html = read(INDEX_PATH)
        cls.sw = read(SW_PATH)

    def test_cache_name_format(self):
        cache = sw_cache_name(self.sw)
        self.assertIsNotNone(cache, "Không tìm thấy CACHE_NAME trong sw.js")
        self.assertRegex(cache, CACHE_RE)

    def test_expected_cache_matches_sw(self):
        cache = sw_cache_name(self.sw)
        expected = expected_cache(self.html)
        self.assertIsNotNone(expected, "Không tìm thấy EXPECTED_CACHE trong index.html")
        self.assertEqual(
            expected,
            cache,
            "CACHE_NAME trong sw.js (%s) và EXPECTED_CACHE trong index.html (%s) đang lệch nhau."
            % (cache, expected),
        )

    def test_all_imported_modules_are_cached(self):
        imported = set(re.findall(r"from\s+['\"]\./([^'\"]+)['\"]", self.html))
        self.assertTrue(imported, "index.html không import module nào?")
        assets = set(sw_assets(self.sw))
        missing = sorted(imported - assets)
        self.assertEqual(
            missing,
            [],
            "Module được import nhưng thiếu trong ASSETS của sw.js: %s" % ", ".join(missing),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
