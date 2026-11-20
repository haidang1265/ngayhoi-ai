"""Fixtures dùng chung cho tất cả các test.

Mỗi test nhận một DB riêng (db_path) và một TestClient trỏ vào DB đó.
Không nạp CSV gốc → dữ liệu test độc lập, tái lập được.
"""
import os

# Đặt LLM_MODE=offline trước khi import bất kỳ module app nào
os.environ["LLM_MODE"] = "offline"
os.environ["AUTH_MODE"] = "demo"

import pytest
from fastapi.testclient import TestClient

import app.config as config_mod
import app.db as csdl
import app.main as main_module

# ── hằng số test ─────────────────────────────────────────────────────────────
ADMIN_KEY_TEST = "test-admin"
# THOI_DIEM giả lập: trước ngày hội 2026-11-13 đủ xa (>24 giờ) → cho phép hủy
THOI_DIEM_TEST = "2026-11-01T10:00:00"

# 12 phiên theo data/phien.csv
PHIEN_DATA = [
    ("P01", "Kỹ sư phần mềm Web",          "Công ty A", "Phần mềm",   "2026-11-13T08:00:00", "Hội trường A", 30),
    ("P02", "Kỹ sư dữ liệu",               "Công ty B", "Dữ liệu",    "2026-11-13T08:00:00", "Phòng B201",   30),
    ("P03", "Kỹ sư hệ thống nhúng",         "Công ty C", "Nhúng-IoT",  "2026-11-13T09:00:00", "Hội trường A", 30),
    ("P04", "An toàn thông tin",            "Công ty D", "An ninh mạng","2026-11-13T09:00:00", "Phòng B201",   30),
    ("P05", "Kỹ sư AI ứng dụng",           "Công ty E", "AI",          "2026-11-13T10:00:00", "Hội trường A", 30),
    ("P06", "Kiểm thử phần mềm",           "Công ty F", "Phần mềm",   "2026-11-13T10:00:00", "Phòng B201",   30),
    ("P07", "Phân tích nghiệp vụ",         "Công ty G", "Dữ liệu",    "2026-11-13T13:30:00", "Hội trường A", 30),
    ("P08", "Kỹ sư điện toán đám mây",     "Công ty H", "Hạ tầng",    "2026-11-13T13:30:00", "Phòng B201",   30),
    ("P09", "Lập trình di động",           "Công ty I", "Phần mềm",   "2026-11-13T14:30:00", "Hội trường A", 30),
    ("P10", "Kỹ sư MLOps",                "Công ty K", "AI",          "2026-11-13T14:30:00", "Phòng B201",   30),
    ("P11", "Quản trị mạng",              "Công ty L", "Hạ tầng",    "2026-11-13T15:30:00", "Hội trường A", 30),
    ("P12", "Thực tập kỹ sư cầu nối",     "Công ty M", "Phần mềm",   "2026-11-13T15:30:00", "Phòng B201",   30),
]

# 10 sinh viên test (không có trong CSV gốc)
SV_DATA = [
    (f"TT{i:06d}", f"Sinh viên test {i:02d}", "BCSE-TEST")
    for i in range(1, 11)
]


def _seed_db(db_path: str) -> None:
    """Khởi tạo DB test với sinh viên và phiên mẫu."""
    db = csdl.ket_noi(db_path)
    for sv in SV_DATA:
        db.execute(
            "INSERT OR IGNORE INTO sinh_vien (ma_sv, ho_ten, lop) VALUES (?, ?, ?)", sv)
    for p in PHIEN_DATA:
        db.execute(
            "INSERT OR IGNORE INTO phien "
            "(ma_phien, chu_de, doanh_nghiep, linh_vuc, gio_bat_dau, phong, suc_chua) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", p)
    db.close()


@pytest.fixture
def db_path(tmp_path):
    """Trả về đường dẫn tới DB test đã được seed."""
    p = str(tmp_path / "test.db")
    _seed_db(p)
    return p


@pytest.fixture
def client(db_path, monkeypatch):
    """TestClient trỏ vào DB test; override lay_db và config."""
    monkeypatch.setattr(config_mod, "DB_PATH", db_path)
    monkeypatch.setattr(config_mod, "THOI_DIEM", THOI_DIEM_TEST)
    monkeypatch.setattr(config_mod, "ADMIN_KEY", ADMIN_KEY_TEST)

    def override_lay_db():
        db = csdl.ket_noi(db_path)
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[main_module.lay_db] = override_lay_db

    # raise_server_exceptions=False để đọc HTTP status thực sự
    with TestClient(main_module.app, raise_server_exceptions=False) as c:
        yield c

    main_module.app.dependency_overrides.clear()
