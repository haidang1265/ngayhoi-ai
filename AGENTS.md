# AGENTS.md — Quy tắc cho AI agent

Tài liệu này định nghĩa phạm vi và quy trình làm việc dành cho AI agent
(GitHub Copilot, Claude, ChatGPT, …) khi đóng góp vào repo này.

---

## 1. Phạm vi được phép sửa (IN SCOPE)

| Thư mục / file | Được phép |
|---|---|
| `tests/` | ✅ Thêm file test mới hoặc test-case mới |
| `app/dang_ky.py` | ✅ Sửa logic nghiệp vụ nếu test yêu cầu |
| `app/main.py` | ✅ Thêm endpoint mới nếu test yêu cầu |
| `app/config.py` | ✅ Thêm hằng số cấu hình |
| `spec.md` | ✅ Cập nhật đặc tả nếu hành vi thay đổi |

---

## 2. Phạm vi KHÔNG được sửa (OUT OF SCOPE)

| File / hành động | Lý do |
|---|---|
| `.github/workflows/test.yml` | CI pipeline — do con người kiểm soát |
| `app/db.py` | Schema DB — thay đổi phá vỡ dữ liệu cũ |
| `requirements.txt` | Thêm dependency phải được review thủ công |
| `AGENTS.md` (file này) | Quy tắc — không tự sửa |
| Xóa hoặc sửa test đang xanh | Không được làm test cũ thất bại |

---

## 3. Quy trình TDD bắt buộc

Agent **PHẢI** tuân thủ vòng lặp Red → Green:

```
1. VIẾT TEST TRƯỚC  — thêm vào tests/
2. CHẠY TEST        — xác nhận test ĐỎ (thất bại đúng lý do)
3. SỬA CODE         — thay đổi nhỏ nhất để test XANH
4. CHẠY LẠI        — toàn bộ test suite phải xanh
5. COMMIT           — một commit cho test, một commit cho code
```

> ⚠️ Agent **không được** commit code sản phẩm trước khi có test tương ứng.

---

## 4. Giới hạn kích thước PR

- Mỗi PR của agent: **diff ≤ 200 dòng** (thêm + xóa gộp lại).
- Nếu tính năng lớn hơn, chia thành nhiều PR nhỏ.

---

## 5. Lệnh kiểm tra trước khi commit

```bash
AUTH_MODE=demo LLM_MODE=offline pytest tests/ -v
```

Tất cả test phải **PASSED** trước khi tạo commit.

---

## 6. Quy tắc commit message

```
<loại>: <mô tả ngắn gọn bằng tiếng Việt>

Ví dụ:
test: thêm test cho endpoint /api/con-cho
feat: trả về số chỗ còn lại theo ma_phien
fix: sửa lỗi đếm chỗ khi ma_phien không tồn tại
```

---

## 7. Môi trường chạy test

| Biến | Giá trị khi test |
|---|---|
| `AUTH_MODE` | `demo` (bỏ qua xác thực sinh viên) |
| `LLM_MODE` | `offline` (không gọi API LLM thật) |
| DB | SQLite in-memory, tạo lại mỗi test |
