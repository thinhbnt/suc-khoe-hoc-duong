"""Kiểm thử cơ chế TỰ ĐỘNG CẬP NHẬT phiên bản (Service Worker + banner hỏi người dùng).

Lỗi cần chặn: app đã cài (PWA) cứ chạy mãi bản cũ vì
  (1) Service Worker không có `skipWaiting`/`activate` nên bản mới chỉ kích hoạt khi
      người dùng đóng hết tab — thực tế là không bao giờ;
  (2) `fetch` trả cache trước cho cả trang HTML nên HTML cũ nằm lại trong cache;
  (3) giao diện không có chỗ nào HỎI người dùng cập nhật.

Hành vi thật (bấm nút, tải lại trang) được kiểm tra ở e2e.js; file này giữ các
"hợp đồng" tĩnh trong sw.js và index.html.
"""
import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")
SW_PATH = os.path.join(ROOT, "sw.js")


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class TestServiceWorkerUpdate(unittest.TestCase):
    """sw.js phải tự kích hoạt bản mới và phục vụ HTML theo kiểu network-first."""

    @classmethod
    def setUpClass(cls):
        cls.sw = read(SW_PATH)

    def test_install_skips_waiting(self):
        install = re.search(r'addEventListener\("install".*?\n\}\);', self.sw, re.S)
        self.assertIsNotNone(install, "Không tìm thấy handler \"install\" trong sw.js")
        self.assertIn(
            "skipWaiting",
            install.group(0),
            "install phải gọi self.skipWaiting() — nếu không, người đã cài app phải "
            "đóng hết tab mới nhận bản mới.",
        )

    def test_activate_cleans_old_caches_and_claims_clients(self):
        activate = re.search(r'addEventListener\("activate".*?\n\}\);', self.sw, re.S)
        self.assertIsNotNone(activate, "Thiếu handler \"activate\" trong sw.js")
        body = activate.group(0)
        self.assertIn("caches.delete", body, "activate phải xoá cache của phiên bản cũ")
        self.assertIn("clients.claim", body, "activate phải gọi clients.claim() để nhận tab đang mở")
        self.assertIn("health-pwa-", body, "chỉ nên xoá cache cùng tiền tố health-pwa-")
        self.assertIn("SW_ACTIVATED", body, "activate nên báo cho trang biết để vẽ lại footer/banner")

    def test_message_channel_allows_immediate_activation(self):
        self.assertRegex(
            self.sw,
            re.compile(r'addEventListener\("message".*?SKIP_WAITING', re.S),
            "sw.js phải nghe message SKIP_WAITING để nút \"Cập nhật ngay\" kích hoạt được ngay.",
        )

    def test_navigation_is_network_first(self):
        fetch = re.search(r'addEventListener\("fetch".*?\n\}\);', self.sw, re.S)
        self.assertIsNotNone(fetch, "Thiếu handler \"fetch\" trong sw.js")
        body = fetch.group(0)
        self.assertIn('"navigate"', body, "phải nhận diện request điều hướng (mode === 'navigate')")
        # Trang HTML: gọi fetch(e.request) TRƯỚC khi đọc cache, và vẫn có cache dự phòng.
        self.assertRegex(
            body,
            r"fetch\(e\.request\)[\s\S]*caches\.match",
            "với trang HTML phải thử mạng trước rồi mới dùng cache (offline mới cần cache).",
        )
        self.assertIn('caches.match("./index.html")', body, "phải có cache dự phòng cho trang chủ khi offline")

    def test_static_assets_still_cache_first(self):
        fetch = re.search(r'addEventListener\("fetch".*?\n\}\);', self.sw, re.S)
        body = fetch.group(0)
        self.assertRegex(
            body,
            r"caches\.match\(e\.request\)\.then\(\(res\) => res \|\| fetch\(e\.request\)\)",
            "tài nguyên tĩnh vẫn phải ưu tiên cache để chạy offline.",
        )


class TestUpdateUi(unittest.TestCase):
    """index.html phải có banner hỏi người dùng, tự kiểm tra và chỉ tải lại khi đồng ý."""

    @classmethod
    def setUpClass(cls):
        cls.html = read(INDEX_PATH)

    def test_banner_markup_exists_and_hidden_by_default(self):
        self.assertRegex(
            self.html,
            r'<div id="updateBanner"[^>]*\bhidden\b',
            "Banner cập nhật #updateBanner phải có sẵn trong HTML và mặc định ẩn (hidden).",
        )
        ids = ("updateBannerText", "btnUpdateNow", "btnUpdateLater", "btnCheckUpdate", "swCheck")
        for element_id in ids:
            self.assertIn('id="%s"' % element_id, self.html, "Thiếu #%s" % element_id)
        self.assertIn("Cập nhật ngay", self.html, "Nút trong banner phải ghi rõ \"Cập nhật ngay\"")
        self.assertIn("Để sau", self.html, "Phải có lựa chọn \"Để sau\" để không bị ép tải lại")

    def test_register_disables_http_cache_for_sw(self):
        self.assertRegex(
            self.html,
            r"register\('\./sw\.js', \{ updateViaCache: 'none' \}\)",
            "Phải đăng ký sw.js với updateViaCache: 'none' — nếu không, chính file sw.js bị "
            "HTTP cache giữ lại và việc kiểm tra bản mới bị trễ tới 10 phút.",
        )

    def test_listens_for_new_versions(self):
        for token in ("updatefound", "controllerchange", "reg.waiting", "swReg.waiting"):
            self.assertIn(token, self.html, "Thiếu xử lý %s → có bản mới mà giao diện không biết." % token)
        self.assertRegex(
            self.html,
            r"swReg\.update\(\)",
            "Phải gọi registration.update() để chủ động hỏi bản mới (nút + tự động).",
        )

    def test_no_silent_reload_while_typing(self):
        # Chỉ tải lại sau khi người dùng bấm "Cập nhật ngay" (userAcceptedUpdate),
        # tránh mất dữ liệu đang nhập và tránh vòng lặp reload.
        self.assertIn("userAcceptedUpdate", self.html)
        change = re.search(r"controllerchange', \(\) => \{.*?\n      \}\);", self.html, re.S)
        self.assertIsNotNone(change, "Thiếu listener 'controllerchange'")
        self.assertIn(
            "userAcceptedUpdate",
            change.group(0),
            "Chỉ được location.reload() khi người dùng đã đồng ý cập nhật.",
        )
        self.assertIn("reloading", self.html, "Cần cờ chống tải lại nhiều lần (vòng lặp reload).")

    def test_periodic_and_visibility_checks(self):
        self.assertRegex(
            self.html,
            r"SW_CHECK_INTERVAL\s*=\s*15\s*\*\s*60\s*\*\s*1000",
            "Phải tự kiểm tra định kỳ (15 phút) chứ không chỉ lúc mở app.",
        )
        self.assertIn("setInterval", self.html, "Thiếu setInterval để kiểm tra định kỳ.")
        self.assertIn(
            "visibilitychange",
            self.html,
            "Phải kiểm tra lại khi người dùng quay lại tab (app PWA hay bị để nền).",
        )
        self.assertIn(
            "getRegistration()",
            self.html,
            "Nút \"Kiểm tra cập nhật\" phải lấy được registration hiện có.",
        )


    def test_banner_sits_at_top_of_page(self):
        head, _, _ = self.html.partition('<script type="module">')
        banner_at = head.find('id="updateBanner"')
        first_card = head.find('<div class="card">')
        body_at = head.find('<body>')
        self.assertGreater(banner_at, -1, "Thiếu #updateBanner")
        self.assertGreater(first_card, -1, "Không tìm thấy card nội dung đầu tiên")
        self.assertLess(
            body_at,
            banner_at,
            "Thanh cập nhật phải nằm trong <body>, ngay đầu trang.",
        )
        self.assertLess(
            banner_at,
            first_card,
            "Thanh cập nhật phải đứng TRƯỚC nội dung (đầu trang), không phải ở cuối trang.",
        )

    def test_banner_css_is_in_flow_and_sticky_at_top(self):
        rule = re.search(r"\.update-banner\s*\{([^}]*)\}", self.html)
        self.assertIsNotNone(rule, "Thiếu CSS .update-banner")
        css = rule.group(1)
        self.assertIn("position: sticky", css, "Thanh cập nhật phải nằm trong luồng trang (sticky) ở đầu trang.")
        self.assertIn("top: 0", css, "Thanh cập nhật phải dính mép trên khi người dùng cuộn xuống.")
        self.assertNotIn("position: fixed", css, "Không dùng fixed nữa — fixed che mất nội dung đầu trang.")
        self.assertNotIn("bottom:", css, "Thanh cập nhật không còn nằm ở đáy màn hình.")
        self.assertIn("max-width: 480px", css, "Bề rộng phải khớp .card/.app-footer (480px) để không lệch layout.")
        self.assertIn("[hidden]", self.html, "Phải giữ .update-banner[hidden] { display: none } để ẩn hoàn toàn.")

    def test_banner_is_polite_live_region(self):
        tag = re.search(r'<div id="updateBanner"[^>]*>', self.html)
        self.assertIsNotNone(tag, "Thiếu thẻ #updateBanner")
        attrs = tag.group(0)
        self.assertIn('aria-live="polite"', attrs, "Dùng aria-live=polite để không cắt ngang câu trình đọc màn hình đang đọc.")
        self.assertIn('role="status"', attrs, "Vùng thông báo nên dùng role=status.")

    def test_later_dismiss_remembered_for_session(self):
        self.assertIn("sessionStorage", self.html, "Phải ghi nhớ lựa chọn bằng sessionStorage.")
        self.assertIn("UPDATE_LATER_KEY", self.html, "Thiếu hằng khoá ghi nhớ 'Để sau'.")
        self.assertRegex(
            self.html,
            r"storageSet\(UPDATE_LATER_KEY, '1'\)",
            'Nút "Để sau" phải ghi nhớ để thanh không bật lại sau mỗi 15 phút.',
        )
        self.assertRegex(
            self.html,
            r"storageGet\(UPDATE_LATER_KEY\) === '1'",
            "showUpdateBanner phải bỏ qua khi người dùng đã chọn Để sau trong phiên này.",
        )
        self.assertRegex(
            self.html,
            r"storageRemove\(UPDATE_LATER_KEY\)",
            'Nút "Kiểm tra cập nhật" phải xoá ghi nhớ để thanh hiện lại nếu có bản mới.',
        )

    def test_app_badge_when_supported(self):
        self.assertIn("navigator.setAppBadge", self.html, "Nên bật chấm đỏ trên icon app đã cài khi có bản mới.")
        self.assertIn("navigator.clearAppBadge", self.html, "Phải tắt chấm đỏ sau khi cập nhật xong.")
        self.assertRegex(
            self.html,
            r"typeof fn !== 'function'",
            "Badging API không có ở mọi trình duyệt (Safari/Firefox) → phải kiểm tra tồn tại trước khi gọi.",
        )

    def test_reload_fallback_when_update_hangs(self):
        self.assertRegex(
            self.html,
            r"RELOAD_FALLBACK_MS\s*=\s*8000",
            "Cần hẹn giờ dự phòng (8 giây) khi bấm Cập nhật ngay mà không tải lại được.",
        )
        self.assertRegex(self.html, r"btnNow\.disabled = true", "Trong lúc cập nhật phải khoá nút để tránh bấm nhiều lần.")
        self.assertIn("Đang cập nhật…", self.html, 'Phải hiện trạng thái "Đang cập nhật…".')
        self.assertIn("Tải lại trang", self.html, "Hết thời gian chờ phải có nút dự phòng để người dùng không bị kẹt.")

    def test_confirms_right_after_updating(self):
        self.assertIn("UPDATED_FROM_KEY", self.html, "Phải ghi lại phiên bản trước khi tải lại.")
        self.assertRegex(
            self.html,
            r"Đã cập nhật lên v\$\{APP_VERSION\}",
            'Sau khi tải lại phải báo "Đã cập nhật lên v…" để người dùng biết đã xong.',
        )
        self.assertIn("showUpdatedToast();", self.html, "Phải gọi showUpdatedToast() khi trang khởi động.")


if __name__ == "__main__":
    unittest.main()
