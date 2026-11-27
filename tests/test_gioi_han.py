"""tests/test_gioi_han.py — 5 test case từ spec.md (hàng 1–5).
Hàng 6 (40 người đồng lúc) → scripts/ban_dong_thoi.py.
"""
import os, sqlite3, pytest

os.environ.setdefault("LLM_MODE", "offline")
os.environ.setdefault("AUTH_MODE", "demo")

import app.config as config_mod
import app.db as csdl
import app.main as main_module
from fastapi.testclient import TestClient

# ---- dữ liệu hạt giống ----
_PHIEN = [
    ("P01", "Kỹ sư phần mềm Web", "Công ty A", "Phần mềm", "2026-11-13T08:00:00", "Hội trường A", 30),
    ("P02", "Kỹ sư dữ liệu",      "Công ty B", "Dữ liệu",  "2026-11-13T08:00:00", "Phòng B201",   30),
]

def _seed(db_path: str):
    db = csdl.ket_noi(db_path)
    db.execute("INSERT OR IGNORE INTO sinh_vien (ma_sv, ho_ten, lop) VALUES ('SV000','Sinh viên 0','TEST')")
    for p in _PHIEN:
        db.execute(
            "INSERT OR IGNORE INTO phien "
            "(ma_phien,chu_de,doanh_nghiep,linh_vuc,gio_bat_dau,phong,suc_chua) VALUES (?,?,?,?,?,?,?)", p)
    db.commit(); db.close()

def _lap_day(db_path: str, ma_phien: str, n: int):
    """Chèn n sinh viên giả vào phiên ma_phien để kiểm tra giới hạn."""
    db = csdl.ket_noi(db_path)
    for i in range(n):
        db.execute("INSERT OR IGNORE INTO sinh_vien (ma_sv, ho_ten, lop) VALUES (?,?,?)",
                   (f"XX{i:06d}", f"test {i}", "TEST"))
        db.execute("INSERT OR IGNORE INTO dang_ky (ma_sv, ma_phien) VALUES (?,?)",
                   (f"XX{i:06d}", ma_phien))
    db.commit(); db.close()

# ---- fixtures ----

@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    _seed(p)
    return p

@pytest.fixture
def client(db_path, monkeypatch):
    monkeypatch.setattr(config_mod, "DB_PATH", db_path)
    monkeypatch.setattr(config_mod, "THOI_DIEM", "2026-11-01T10:00:00")

    def _lay_db():
        db = csdl.ket_noi(db_path)
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[main_module.lay_db] = _lay_db
    with TestClient(main_module.app, raise_server_exceptions=False) as c:
        yield c
    main_module.app.dependency_overrides.clear()


# ---- test cases ----

AUTH = {"X-Ma-SV": "SV000"}


class TestGioiHanCho:

    def test_1_p01_trong_dang_ky_duoc(self, client):
        """Hàng 1 — P01 trống: đăng ký → 201."""
        r = client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P01"})
        assert r.status_code == 201

    def test_2_p01_co_29_con_1_cho(self, client, db_path):
        """Hàng 2 — P01 có 29 chỗ đã đặt: SV mới → 201 (vẫn còn 1 chỗ cuối)."""
        _lap_day(db_path, "P01", 29)
        r = client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P01"})
        assert r.status_code == 201

    def test_3_p01_het_cho(self, client, db_path):
        """Hàng 3 — P01 đủ 30: SV mới → 409 HET_CHO."""
        _lap_day(db_path, "P01", 30)
        r = client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P01"})
        assert r.status_code == 409
        assert r.json()["detail"] == "HET_CHO"

    def test_4_p01_full_da_dang_ky(self, client, db_path):
        """Hàng 4 — P01 đầy (gồm SV000): SV000 đăng ký lại → 409 DA_DANG_KY (kiểm trước HET_CHO)."""
        _lap_day(db_path, "P01", 29)                    # 29 sinh viên khác
        client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P01"})  # SV000 → 30, hết chỗ
        r = client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P01"})  # thử lại
        assert r.status_code == 409
        assert r.json()["detail"] == "DA_DANG_KY"

    def test_5_p01_het_p02_van_con(self, client, db_path):
        """Hàng 5 — P01 đầy 30: SV000 đăng ký P02 → 201 (đếm riêng từng phiên)."""
        _lap_day(db_path, "P01", 30)
        r = client.post("/api/dang-ky", headers=AUTH, json={"ma_phien": "P02"})
        assert r.status_code == 201
