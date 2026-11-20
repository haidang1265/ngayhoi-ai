"""14 test cases kiểm thử các endpoint còn lại của API.

test_api_01  : GET  /api/trang-thai → 200, có trường llm/auth/so_sinh_vien
test_api_02  : GET  /api/phien → 200, kết quả là list
test_api_03  : GET  /api/phien với X-Ma-SV → có trường da_dang_ky
test_api_04  : GET  /api/con-cho?ma_phien=P05 → 200, con_cho = 30
test_api_05  : GET  /api/con-cho?ma_phien=ZZZZ → 404
test_api_06  : GET  /api/toi không có auth → 401
test_api_07  : GET  /api/toi với auth hợp lệ → 200, có ma_sv
test_api_08  : POST /api/hoi câu hỏi hợp lệ → 200, có tra_loi
test_api_09  : POST /api/hoi câu hỏi quá ngắn (< 3 ký tự) → 422
test_api_10  : GET  /api/thong-ke không có admin key → 403
test_api_11  : GET  /api/thong-ke với admin key → 200, có ho_so/chi_so
test_api_12  : POST /api/cong-diem không có admin key → 403
test_api_13  : POST /api/cong-diem với admin key → 200, có du_dieu_kien
test_api_14  : POST /api/poster không có admin key → 403
"""
from tests.conftest import ADMIN_KEY_TEST

HDR_SV = {"X-Ma-SV": "TT000003"}
HDR_ADM = {"X-Admin-Key": ADMIN_KEY_TEST}


class TestEndpoints:
    """14 test cases kiểm thử API ngoài phần đăng ký."""

    # test_api_01 ─────────────────────────────────────────────────────────────
    def test_api_01_trang_thai(self, client):
        """GET /api/trang-thai → 200, trả về trạng thái hệ thống."""
        r = client.get("/api/trang-thai")
        assert r.status_code == 200
        d = r.json()
        assert "llm" in d
        assert "auth" in d
        assert "so_sinh_vien" in d

    # test_api_02 ─────────────────────────────────────────────────────────────
    def test_api_02_phien_list(self, client):
        """GET /api/phien → 200, trả về danh sách 12 phiên."""
        r = client.get("/api/phien")
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        assert len(lst) == 12

    # test_api_03 ─────────────────────────────────────────────────────────────
    def test_api_03_phien_with_masv(self, client):
        """GET /api/phien với X-Ma-SV → mỗi phiên có trường da_dang_ky."""
        r = client.get("/api/phien", headers=HDR_SV)
        assert r.status_code == 200
        lst = r.json()
        assert all("da_dang_ky" in p for p in lst)
        # SV chưa đăng ký → tất cả da_dang_ky = False
        assert all(p["da_dang_ky"] is False for p in lst)

    # test_api_04 ─────────────────────────────────────────────────────────────
    def test_api_04_con_cho_hop_le(self, client):
        """GET /api/con-cho?ma_phien=P05 → 200, con_cho = 30 (chưa ai đăng ký)."""
        r = client.get("/api/con-cho", params={"ma_phien": "P05"})
        assert r.status_code == 200
        assert r.json()["con_cho"] == 30

    # test_api_05 ─────────────────────────────────────────────────────────────
    def test_api_05_con_cho_phien_khong_ton_tai(self, client):
        """GET /api/con-cho với mã phiên không tồn tại → 404."""
        r = client.get("/api/con-cho", params={"ma_phien": "ZZZZ"})
        assert r.status_code == 404

    # test_api_06 ─────────────────────────────────────────────────────────────
    def test_api_06_toi_chua_dang_nhap(self, client):
        """GET /api/toi không có X-Ma-SV → 401."""
        r = client.get("/api/toi")
        assert r.status_code == 401

    # test_api_07 ─────────────────────────────────────────────────────────────
    def test_api_07_toi_co_auth(self, client):
        """GET /api/toi với X-Ma-SV hợp lệ → 200, có trường ma_sv."""
        r = client.get("/api/toi", headers=HDR_SV)
        assert r.status_code == 200
        assert r.json()["ma_sv"] == "TT000003"

    # test_api_08 ─────────────────────────────────────────────────────────────
    def test_api_08_hoi_hop_le(self, client):
        """POST /api/hoi câu hỏi hợp lệ → 200, có trường tra_loi và nguon."""
        r = client.post("/api/hoi", json={"cau_hoi": "Sức chứa mỗi phiên là bao nhiêu?"})
        assert r.status_code == 200
        d = r.json()
        assert "tra_loi" in d
        assert "nguon" in d

    # test_api_09 ─────────────────────────────────────────────────────────────
    def test_api_09_hoi_cau_hoi_qua_ngan(self, client):
        """POST /api/hoi với chuỗi < 3 ký tự → 422 Unprocessable Entity."""
        r = client.post("/api/hoi", json={"cau_hoi": "ab"})
        assert r.status_code == 422

    # test_api_10 ─────────────────────────────────────────────────────────────
    def test_api_10_thong_ke_khong_admin(self, client):
        """GET /api/thong-ke không có X-Admin-Key → 403."""
        r = client.get("/api/thong-ke")
        assert r.status_code == 403

    # test_api_11 ─────────────────────────────────────────────────────────────
    def test_api_11_thong_ke_co_admin(self, client):
        """GET /api/thong-ke với admin key hợp lệ → 200, có các trường thống kê."""
        r = client.get("/api/thong-ke", headers=HDR_ADM)
        assert r.status_code == 200
        d = r.json()
        assert "ho_so" in d
        assert "chi_so" in d
        assert "theo_phien" in d

    # test_api_12 ─────────────────────────────────────────────────────────────
    def test_api_12_cong_diem_khong_admin(self, client):
        """POST /api/cong-diem không có X-Admin-Key → 403."""
        r = client.post("/api/cong-diem")
        assert r.status_code == 403

    # test_api_13 ─────────────────────────────────────────────────────────────
    def test_api_13_cong_diem_co_admin(self, client):
        """POST /api/cong-diem với admin key → 200, có trường du_dieu_kien."""
        r = client.post("/api/cong-diem", headers=HDR_ADM)
        assert r.status_code == 200
        d = r.json()
        assert "du_dieu_kien" in d
        assert "cong_moi" in d

    # test_api_14 ─────────────────────────────────────────────────────────────
    def test_api_14_poster_khong_admin(self, client):
        """POST /api/poster không có X-Admin-Key → 403."""
        r = client.post("/api/poster")
        assert r.status_code == 403
