# Output: /compare-content-seo-competitor

## Thông tin chạy thử

- **Skill:** `/compare-content-seo-competitor`
- **Trạng thái:** ✅ Chạy thành công — crawl 4 URL, phân tích đủ 6 mục

---

## Đầu vào

| Loại | URL |
|------|-----|
| Brand | https://osakar.com.vn/tin-tuc/xe-may-dien-cho-hoc-sinh-cap-3/ |
| Đối thủ 1 | https://xedienvietthanh.com/tin-tuc/xe-may-dien-cho-hoc-sinh-cap-3/ |
| Đối thủ 2 | https://xedienmove.vn/tin-tuc/kinh-nghiem-mua-xe-may-dien/xe-may-dien-hoc-sinh-cap-3 |
| Đối thủ 3 | https://tearu.vn/mau-xe-may-dien-cho-hoc-sinh-cap-3/ |

---

## Kết quả crawl

| Nguồn | Domain | Số từ | Heading | Bảng | Danh sách |
|-------|--------|-------|---------|------|-----------|
| Brand | osakar.com.vn | 12.445 | 20 | ✅ | ✅ |
| Đối thủ 1 | xedienvietthanh.com | 1.428 | 31 | ❌ | ✅ |
| Đối thủ 2 | xedienmove.vn | 1.733 | 24 | ✅ | ✅ |
| Đối thủ 3 | tearu.vn | 1.426 | 12 | ❌ | ✅ |

---

## Báo cáo phân tích (6 mục)

### 3.1 Heading / Section còn thiếu

Brand đã phủ gần đủ các section chính. Điểm thiếu đáng chú ý:
- Không có mục **"Xu hướng / Tại sao học sinh cấp 3 nên dùng xe điện"** (angle mở đầu hook người đọc — có ở xedienvietthanh.com)

### 3.2 So sánh độ dài bài viết

| Nguồn | Số từ | So với brand |
|-------|-------|-------------|
| Brand | 12.445 | — |
| Đối thủ 1 | 1.428 | -11.017 từ |
| Đối thủ 2 | 1.733 | -10.712 từ |
| Đối thủ 3 | 1.426 | -11.019 từ |
| **Trung bình đối thủ** | **~1.529** | **Brand dài hơn 8,1×** |

> ⚠️ Brand dài hơn đối thủ 8 lần. Phần lớn lượng từ đến từ mô tả spec lặp lại ("đạt chuẩn" ×61, "vượt chuẩn" ×57).

### 3.3 Định dạng brand đang thiếu

| Định dạng | Brand | ≥2 đối thủ? | Gợi ý |
|-----------|-------|-------------|-------|
| Ordered list (ol) | ❌ | 1/3 | Không bắt buộc |
| FAQ | ❌ | 0/3 | **Cơ hội blue ocean** |
| Kết luận | ❌ | 0/3 | Nên thêm dù đối thủ chưa làm |
| Mục lục (TOC) | ❌ | 0/3 | **Bài 12k từ mà không có TOC = UX thảm hoạ** |

### 3.4 LSI Keyword cần bổ sung (top 8)

| # | Keyword | Có ở đối thủ | Chèn vào |
|---|---------|-------------|----------|
| 1 | chất lượng | 2/3 | Tiêu chí chọn mua |
| 2 | mẫu (xe) | 3/3 | Tiêu đề H2, mở đầu section |
| 3 | lựa chọn | 2/3 | Sapo, kết luận |
| 4 | hiện đại | 2/3 | Mô tả thiết kế |
| 5 | bảo hành | 2/3 | Lưu ý khi mua |
| 6 | công suất | 2/3 | Tiêu chí kỹ thuật |
| 7 | dòng xe | 2/3 | Mục giới thiệu sản phẩm |
| 8 | tính năng | 2/3 | Bullet spec |

### 3.5 Bigram brand chưa đề cập

| # | Cụm từ | Có ở đối thủ |
|---|--------|-------------|
| 1 | mẫu máy | 3/3 — quan trọng nhất |
| 2 | chất lượng | 2/3 |
| 3 | lựa chọn | 2/3 |
| 4 | hiện đại | 2/3 |

### 3.6 Mật độ từ khoá chính

| Nguồn | "học sinh" (%) | "máy điện" (%) |
|-------|---------------|---------------|
| Brand | 1,03% | 1,01% |
| Trung bình đối thủ | 1,12% | 2,64% |

> Brand đang **under-optimize** cụm "xe máy điện" so với đối thủ (1,01% vs 2,64%).

---

## TOP 5 VIỆC CẦN LÀM NGAY

```
🔴 [Cao]   Thêm Mục lục (TOC) — bài 12k từ thiếu TOC làm tăng bounce rate
🔴 [Cao]   Rút gọn mô tả spec lặp → thay bằng bảng so sánh
🟡 [Trung] Thêm phần Kết luận + chèn lại keyword
🟡 [Trung] Tích hợp bigram "mẫu máy" vào H2 và sapo
🟢 [Thấp]  Tạo mục FAQ 3–5 câu để bắt featured snippet
```
