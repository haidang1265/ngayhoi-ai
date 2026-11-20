"""10 test cases đặc tả từ spec.md — kiểm thử nghiệp vụ đăng ký / hủy đăng ký.

test_1  : đăng ký vào P05 mới → 201
test_2  : P01 có 29 chỗ đã đặt → đặt thêm → 201
test_3  : P01 đủ 30 → đặt thêm → 409 HET_CHO
test_4  : SV đã đăng ký P01 → đăng ký lại → 409 DA_DANG_KY
test_5  : hai SV khác nhau đếm riêng → đều 201
test_6  : SV đã có 3 phiên → đăng ký thêm → 409 QUA_SO_PHIEN
test_7  : thiếu trường ma_phien → 422
test_8  : chưa đăng nhập → 401
test_9  : hủy khi không có đăng ký → 404 KHONG_CO
test_10 : hủy trước >24 giờ → 200
"""
import app.db as csdl

SV1 = "TT000001"
SV2 = "TT000002"
HDR1 = {"X-Ma-SV": SV1}
HDR2 = {"X-Ma-SV": SV2}


def _fill_p01(db_path: str, so_luong: int) -> None:
    """Chèn `so_luong` đăng ký giả vào P01 (dùng mã SV tạm thời FAKE...)."""
    db = csdl.ket_noi(db_path)
    for i in range(so_luong):
        ma = f"FAKE{i:04d}"
        db.execute("INSERT OR IGNORE INTO sinh_vien VALUES (?, ?, ?)", (ma, f"Fake {i}", "FAKE"))
        db.execute("INSERT OR IGNORE INTO dang_ky (ma_sv, ma_phien) VALUES (?, ?)", (ma, "P01"))
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
class TestSpec:
    """10 test cases từ spec.md."""

    # test_1 ──────────────────────────────────────────────────────────────────
    def test_1_dang_ky_p05(self, client):
        """Đăng ký vào phiên P05 (trống) → 201 ok."""
        r = client.post("/api/dang-ky", json={"ma_phien": "P05"}, headers=HDR1)
        assert r.status_code == 201
        assert r.json()["ok"] is True
        assert r.json()["ma_phien"] == "P05"

    # test_2 ──────────────────────────────────────────────────────────────────
    def test_2_p01_co_29_con_1_cho(self, client, db_path):
        """P01 đã có 29 đăng ký → đăng ký thêm 1 → 201 (chưa hết chỗ)."""
        _fill_p01(db_path, 29)
        r = client.post("/api/dang-ky", json={"ma_phien": "P01"}, headers=HDR1)
        assert r.status_code == 201

    # test_3 ──────────────────────────────────────────────────────────────────
    def test_3_p01_het_cho(self, client, db_path):
        """P01 đã có 30 đăng ký → đăng ký tiếp → 409 HET_CHO."""
        _fill_p01(db_path, 30)
        r = client.post("/api/dang-ky", json={"ma_phien": "P01"}, headers=HDR1)
        assert r.status_code == 409
        assert r.json()["detail"] == "HET_CHO"

    # test_4 ──────────────────────────────────────────────────────────────────
    def test_4_da_dang_ky(self, client, db_path):
        """SV đã đăng ký P01 → đăng ký lại cùng phiên → 409 DA_DANG_KY."""
        db = csdl.ket_noi(db_path)
        db.execute("INSERT INTO dang_ky (ma_sv, ma_phien) VALUES (?, ?)", (SV1, "P01"))
        db.close()
        r = client.post("/api/dang-ky", json={"ma_phien": "P01"}, headers=HDR1)
        assert r.status_code == 409
        assert r.json()["detail"] == "DA_DANG_KY"

    # test_5 ──────────────────────────────────────────────────────────────────
    def test_5_sv_khac_nhau_dem_rieng(self, client, db_path):
        """SV1 đăng ký P01 và P05; SV2 đăng ký P01 → đều thành công (đếm riêng)."""
        db = csdl.ket_noi(db_path)
        db.execute("INSERT INTO dang_ky (ma_sv, ma_phien) VALUES (?, ?)", (SV1, "P01"))
        db.close()
        # SV2 đăng ký P01 — số lượng P01 = 1 (SV1) < 30
        r2 = client.post("/api/dang-ky", json={"ma_phien": "P01"}, headers=HDR2)
        assert r2.status_code == 201
        # SV1 đăng ký P05 — phiên riêng, không ảnh hưởng P01
        r1 = client.post("/api/dang-ky", json={"ma_phien": "P05"}, headers=HDR1)
        assert r1.status_code == 201

    # test_6 ──────────────────────────────────────────────────────────────────
    def test_6_qua_so_phien(self, client, db_path):
        """SV đã có 3 phiên (tối đa) → đăng ký phiên thứ 4 → 409 QUA_SO_PHIEN."""
        db = csdl.ket_noi(db_path)
        for p in ["P01", "P02", "P03"]:
            db.execute("INSERT INTO dang_ky (ma_sv, ma_phien) VALUES (?, ?)", (SV1, p))
        db.close()
        r = client.post("/api/dang-ky", json={"ma_phien": "P04"}, headers=HDR1)
        assert r.status_code == 409
        assert r.json()["detail"] == "QUA_SO_PHIEN"

    # test_7 ──────────────────────────────────────────────────────────────────
    def test_7_thieu_truong(self, client):
        """Gửi body thiếu ma_phien → 422 Unprocessable Entity."""
        r = client.post("/api/dang-ky", json={}, headers=HDR1)
        assert r.status_code == 422

    # test_8 ──────────────────────────────────────────────────────────────────
    def test_8_chua_dang_nhap(self, client):
        """Không có header X-Ma-SV → 401 CHUA_DANG_NHAP."""
        r = client.post("/api/dang-ky", json={"ma_phien": "P05"})
        assert r.status_code == 401

    # test_9 ──────────────────────────────────────────────────────────────────
    def test_9_huy_khong_co_dang_ky(self, client):
        """DELETE khi SV không có đăng ký P05 → 404 KHONG_CO."""
        r = client.delete("/api/dang-ky/P05", headers=HDR1)
        assert r.status_code == 404
        assert r.json()["detail"] == "KHONG_CO"

    # test_10 ─────────────────────────────────────────────────────────────────
    def test_10_huy_hop_le(self, client, db_path):
        """Hủy đăng ký trước >24 giờ so với giờ bắt đầu phiên → 200 ok.

        THOI_DIEM = 2026-11-01T10:00:00; P05 bắt đầu 2026-11-13T10:00:00 → chênh 12 ngày.
        """
        db = csdl.ket_noi(db_path)
        db.execute("INSERT INTO dang_ky (ma_sv, ma_phien) VALUES (?, ?)", (SV1, "P05"))
        db.close()
        r = client.delete("/api/dang-ky/P05", headers=HDR1)
        assert r.status_code == 200
        assert r.json()["ok"] is True
