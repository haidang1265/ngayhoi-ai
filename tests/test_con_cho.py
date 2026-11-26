"""
Bước 6 — Agent viết test cho endpoint GET /api/con-cho
Quy trình TDD: test đỏ → sửa code → test xanh
(Endpoint và hàm con_cho() đã có sẵn từ Buổi 3)
"""

import os, sqlite3, pytest

os.environ.setdefault("LLM_MODE", "offline")
os.environ.setdefault("AUTH_MODE", "demo")

import app.config as config_mod
import app.db as csdl
import app.main as main_module
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_PHIEN = [
    ("P01", "AI & Robot", "FPT", "CNTT", "2026-11-13T08:00:00", "A101", 5),
    ("P02", "Dữ liệu lớn", "VNG", "Dữ liệu", "2026-11-13T09:00:00", "B202", 10),
]


def _seed(db_path: str):
    db = csdl.ket_noi(db_path)
    # Thêm 1 sinh_vien để lifespan không nạp CSV (sẽ ghi đè phiên test)
    db.execute("INSERT OR IGNORE INTO sinh_vien (ma_sv, ho_ten, lop) VALUES ('__seed__','seed','TEST')")
    for p in _PHIEN:
        db.execute(
            "INSERT OR IGNORE INTO phien "
            "(ma_phien,chu_de,doanh_nghiep,linh_vuc,gio_bat_dau,phong,suc_chua) VALUES (?,?,?,?,?,?,?)",
            p,
        )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Test-cases
# ---------------------------------------------------------------------------

class TestConCho:

    def test_1_phien_trong_tra_ve_suc_chua(self, client):
        """Phiên chưa ai đăng ký → con_cho == sức chứa (5)."""
        r = client.get("/api/con-cho", params={"ma_phien": "P01"})
        assert r.status_code == 200
        body = r.json()
        assert body["ma_phien"] == "P01"
        assert body["con_cho"] == 5

    def test_2_sau_dang_ky_giam_1(self, client, db_path):
        """Sau 1 lần đăng ký → con_cho giảm còn 4."""
        db = csdl.ket_noi(db_path)
        db.execute("INSERT OR IGNORE INTO sinh_vien (ma_sv, ho_ten, lop) VALUES ('SV001','Test SV','TEST')")
        db.execute("INSERT OR IGNORE INTO dang_ky (ma_sv, ma_phien) VALUES ('SV001','P01')")
        db.commit()
        db.close()

        r = client.get("/api/con-cho", params={"ma_phien": "P01"})
        assert r.status_code == 200
        assert r.json()["con_cho"] == 4

    def test_3_phien_khong_ton_tai_tra_404(self, client):
        """Phiên không tồn tại → 404."""
        r = client.get("/api/con-cho", params={"ma_phien": "KHONG_CO"})
        assert r.status_code == 404

    def test_4_ma_phien_khong_phan_biet_hoa_thuong(self, client):
        """ma_phien lowercase → endpoint tự upper(), trả kết quả đúng."""
        r = client.get("/api/con-cho", params={"ma_phien": "p01"})
        assert r.status_code == 200
        assert r.json()["ma_phien"] == "P01"

    def test_5_phan_hoi_du_truong(self, client):
        """Response body phải có đúng hai trường: ma_phien và con_cho."""
        r = client.get("/api/con-cho", params={"ma_phien": "P01"})
        assert r.status_code == 200
        keys = set(r.json().keys())
        assert keys == {"ma_phien", "con_cho"}
