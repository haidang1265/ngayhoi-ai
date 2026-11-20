"""ban_dong_thoi.py — Thí nghiệm 40 người bấm cùng một lúc (Buổi 4, Bước 6–7).

Dùng:
    # Terminal 1 — khởi động máy chủ
    uvicorn app.main:app --reload

    # Terminal 2 — chạy thí nghiệm
    python ban_dong_thoi.py <ma_phien>
    python ban_dong_thoi.py P10

Yêu cầu: AUTH_MODE=demo trong .env (máy chủ nhận bất kỳ mã SV nào).
Kỳ vọng: 201: 30  409: 10
"""
import sys, httpx
from concurrent.futures import ThreadPoolExecutor

PHIEN = sys.argv[1] if len(sys.argv) > 1 else "P10"
URL   = "http://localhost:8000/api/dang-ky"
N     = 40


def gui(i: int) -> int:
    r = httpx.post(
        URL,
        json={"ma_phien": PHIEN},
        headers={"X-Ma-SV": f"TH{i:03d}"},
        timeout=10,
    )
    return r.status_code


with ThreadPoolExecutor(max_workers=N) as ex:
    ket_qua = list(ex.map(gui, range(N)))

print(f"201: {ket_qua.count(201)}  409: {ket_qua.count(409)}")
if ket_qua.count(201) == 30 and ket_qua.count(409) == 10:
    print("✓ Đúng 30/40 — tính năng bảo đảm đúng.")
else:
    print("✗ Kết quả ngoài mong đợi — còn khe hở.")
