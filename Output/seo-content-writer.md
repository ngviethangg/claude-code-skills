# Output: /seo-content-writer

## Thông tin chạy thử

- **Skill:** `/seo-content-writer`
- **Nguồn dữ liệu:** Google Sheets `1_kQ_BPMuUGPd9aeks7RooMR8dBUbUMQSPaw_2FoMVac`
- **Trạng thái:** ✅ Chạy thành công

---

## Đầu vào (đọc từ Google Sheet)

| Cột | Giá trị |
|-----|---------|
| Keyword | xe đạp điện cho học sinh |
| Anchor 1 | xe đạp điện cho học sinh |
| Anchor 2 | xe đạp điện học sinh giá rẻ |
| Chủ đề | xe đạp điện |

---

## Đầu ra

```
✅ Đã viết bài SEO thành công!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Keyword     : xe đạp điện cho học sinh
📐 Độ dài      : ~650 từ
📄 Google Docs : https://docs.google.com/document/d/1BxRmPUw9gZ.../edit
📊 Sheet hàng  : 2 — cột Google Docs URL đã cập nhật
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Luồng xử lý đã thực hiện

1. **BƯỚC 0** — Kiểm tra venv Python 3.13, cài dependencies Google API
2. **BƯỚC 1** — Đọc Google Sheet: lấy keyword + 2 anchor text + chủ đề từ hàng trống (cột F chưa có URL)
3. **BƯỚC 2** — Claude viết bài SEO 500–800 từ theo outline:
   - Tiêu đề: `Xe đạp điện cho học sinh là gì? Gợi ý chọn xe phù hợp nhất`
   - Sapo in nghiêng, keyword in đậm trong sapo
   - 5 H2 không đánh số thứ tự
   - Anchor 1 chèn vào H2 thứ 2, Anchor 2 chèn vào H2 thứ 4
   - Kết luận in nghiêng, keyword in đậm
4. **BƯỚC 3** — Tạo Google Docs qua API, nhận URL, cập nhật vào cột F của sheet

---

## Điểm đã kiểm tra

- [x] Bài đạt 650 từ (nằm trong khung 500–800)
- [x] Keyword có trong title, sapo (in đậm), kết luận (in đậm)
- [x] Sapo và kết luận in nghiêng toàn bộ
- [x] 2 anchor text chèn tự nhiên ở 2 H2 khác nhau
- [x] Không quá 6 H2, không đánh số heading
- [x] Google Docs tạo thành công, URL cập nhật vào sheet
