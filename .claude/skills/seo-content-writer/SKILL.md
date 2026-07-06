---
name: seo-content-writer
description: Viết bài SEO hoàn thiện 500-800 từ từ Google Sheets. Đọc keyword + anchor text từ sheet đầu vào, viết bài theo outline chuẩn (sapo in nghiêng, tối đa 6 H2, kết luận in nghiêng), tạo Google Docs và điền URL vào cột "Google Docs URL". Dùng khi user gõ "viết bài SEO", "tạo content SEO", "viết article cho keyword", hoặc "/seo-content-writer".
when_to_use: |
  Trigger phrases: "viết bài SEO", "tạo content SEO", "viết article cho keyword",
  "chạy skill SEO", "viết content cho keyword", "/seo-content-writer"
user-invokable: true
argument-hint: "[số hàng trong sheet]"
allowed-tools: Bash Read Write
metadata:
  author: nguyenviethangg
  version: "1.0.0"
  category: seo
---

# /seo-content-writer — SEO Content Writer

Viết bài SEO 500-800 từ từ Google Sheets → tạo Google Docs → trả URL về cột "Google Docs URL" trong sheet. **Yêu cầu Claude Code** — không hoạt động trong Claude.ai web chat.

---

## BƯỚC 0 — Bootstrap (chạy tự động lần đầu)

Kiểm tra Python venv:

```bash
test -f ~/.claude/skills/seo-content-writer/.venv/bin/python && echo "READY" || echo "NEED_SETUP"
```

Nếu `NEED_SETUP`, in thông báo cho user rồi chạy:

```bash
bash ~/.claude/skills/seo-content-writer/install.sh 2>&1 | tail -10
```

Kiểm tra `oauth_client.json`. Nếu chưa có, dừng và hướng dẫn user:

> ⚠️ **Chưa có OAuth credentials.** Vào [GCP Console](https://console.cloud.google.com):
> 1. APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
> 2. Enable APIs: **Google Sheets API**, **Google Docs API**, **Google Drive API**
> 3. Download file JSON → đổi tên thành `oauth_client.json` → đặt vào `~/.claude/skills/seo-content-writer/`

---

## BƯỚC 1 — Đọc dữ liệu từ Google Sheets

Lấy hàng chưa xử lý (cột Google Docs URL còn trống):

```bash
~/.claude/skills/seo-content-writer/.venv/bin/python \
  ~/.claude/skills/seo-content-writer/scripts/sheets_handler.py read
```

Nếu user chỉ định hàng cụ thể (vd: `/seo-content-writer 3`):

```bash
~/.claude/skills/seo-content-writer/.venv/bin/python \
  ~/.claude/skills/seo-content-writer/scripts/sheets_handler.py read <số_hàng>
```

Script trả về JSON: `{ "row": 2, "keyword": "...", "anchor1": "...", "anchor2": "...", "topic": "..." }`

Nếu không có hàng nào cần xử lý → thông báo user thêm dữ liệu vào sheet và dừng.

---

## BƯỚC 2 — Viết bài SEO

Dùng `keyword`, `topic`, `anchor1`, `anchor2` từ sheet để viết bài theo **đúng outline sau**:

### 2.1 Tiêu đề
```
[Keyword] là gì? + 1 câu phụ bổ trợ ngắn gọn
```

### 2.2 Sapo *(in nghiêng toàn bộ)*
- Dẫn dắt trực tiếp vào vấn đề
- Chèn **[keyword chính in đậm]** trong khoảng 1.5 dòng đầu
- Độ dài: 2-3 dòng

### 2.3 Thân bài — Các H2
- **Tối đa 6 H2** — chỉ giữ thông tin quan trọng, thực sự cần thiết
- **KHÔNG đánh số heading** (không dùng "1. xxx", "2. xxx", "3. xxx")
- Cấu trúc mỗi H2:
  - Tên mục rõ ràng → nội dung kết hợp text + bullet (insight thực tế người dùng)
  - Đoạn văn: **3-4 dòng**, không bao giờ quá 5 dòng
  - 1-2 placeholder ảnh + caption in nghiêng: ≤70 ký tự, câu đầy đủ chủ-vị, không dấu chấm cuối
- Chèn `anchor1` vào một H2, `anchor2` vào một H2 khác — **không chèn trong sapo và kết luận**

### 2.4 Kết luận *(in nghiêng toàn bộ)*
- Khái quát lại vấn đề
- Chèn **[keyword chính in đậm]**
- Thêm thông tin tham khảo về chủ đề từ TOP 10 Việt Nam và quốc tế

### 2.5 Yêu cầu văn phong
- Dễ hiểu cho người không có nền tảng về `[topic]`
- Không dùng từ hoa mỹ, phô trương; văn phong thông tin, trung thực
- Tổng độ dài: **500-800 từ**

---

## BƯỚC 3 — Tạo Google Docs và cập nhật Sheet

Lưu nội dung bài vào file tạm (thay `[nội dung bài]` bằng toàn bộ bài viết đã tạo):

```bash
cat > /tmp/seo_article_draft.txt << 'ARTICLE_EOF'
[nội dung bài viết đầy đủ]
ARTICLE_EOF
```

Tạo Google Doc từ file tạm:

```bash
cat /tmp/seo_article_draft.txt | \
  ~/.claude/skills/seo-content-writer/.venv/bin/python \
  ~/.claude/skills/seo-content-writer/scripts/sheets_handler.py \
  create-doc "[Keyword] là gì?"
```

Script trả về URL dạng `https://docs.google.com/document/d/DOC_ID/edit`.

Cập nhật URL vào cột F trong sheet:

```bash
~/.claude/skills/seo-content-writer/.venv/bin/python \
  ~/.claude/skills/seo-content-writer/scripts/sheets_handler.py \
  update <row> "<docs_url>"
```

---

## TIÊU CHÍ CHẤT LƯỢNG

Bài đạt yêu cầu khi thoả **tất cả** các điều kiện sau:

- [ ] Tổng 500-800 từ
- [ ] Keyword chính có mặt trong tiêu đề, sapo (in đậm), kết luận (in đậm)
- [ ] Sapo và kết luận in nghiêng hoàn toàn
- [ ] Anchor text 1 và 2 chèn tự nhiên trong 2 H2 khác nhau (không ở sapo/kết luận)
- [ ] Không quá 6 H2; heading không đánh số thứ tự
- [ ] Mỗi đoạn văn 3-4 dòng, không quá 5 dòng
- [ ] Caption ảnh ≤70 ký tự, in nghiêng, câu đầy đủ chủ-vị, không dấu chấm cuối
- [ ] Google Docs đã tạo thành công và URL đã điền vào cột F của sheet

---

## LỖI THƯỜNG GẶP

### Lỗi cài đặt môi trường

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `ensurepip returned non-zero exit status 1` | Python từ Homebrew (3.14) bị lỗi thư viện hệ thống | Dùng Python từ python.org thay thế: `python3.13 -m venv .venv` |
| `ImportError: dlopen ... pyexpat ... Symbol not found` | Python 3.14 Homebrew không tương thích với macOS hiện tại | Cài Python 3.13 từ python.org rồi tạo lại venv |
| `ModuleNotFoundError: No module named 'googleapiclient'` | Chưa cài dependencies hoặc dùng sai Python | Chạy lại: `bash install.sh` |

### Lỗi OAuth / Xác thực

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `oauth_client.json not found` | Chưa đặt file credentials vào đúng thư mục | Đặt file vào `~/.claude/skills/seo-content-writer/oauth_client.json` |
| `403 access_denied` trên trình duyệt | App OAuth đang ở chế độ Testing, email chưa được thêm vào Test Users | GCP → OAuth consent screen → Test users → Add Users → thêm email của bạn |
| `Token expired / invalid_grant` | Token OAuth hết hạn | Xóa `credentials/token.json` rồi chạy lại để xác thực lại |
| `403 Forbidden` từ Google API | Chưa enable đủ 3 API trong GCP | Enable: Sheets API + Docs API + Drive API tại GCP Console |
| Trình duyệt không tự mở khi xác thực | Môi trường không có giao diện đồ họa | Copy URL trong terminal dán thủ công vào trình duyệt |

### Lỗi đọc / ghi dữ liệu

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| Script trả về `[]` | Sheet chưa có hàng dữ liệu nào (chỉ có header) | Điền ít nhất 1 hàng vào sheet trước khi chạy skill |
| `{"error": "no_pending_rows"}` | Tất cả hàng đã có Google Docs URL rồi | Thêm hàng mới vào sheet với cột F để trống |
| `Quota exceeded` | Vượt giới hạn API miễn phí của Google | Đợi 1–2 phút rồi thử lại |
| URL không được điền vào sheet | Script `update` bị lỗi sau khi tạo Docs thành công | Chạy thủ công: `python sheets_handler.py update <row> "<url>"` |

### Lỗi nội dung bài viết

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| Bài quá ngắn (dưới 500 từ) | Keyword quá hẹp hoặc topic ít thông tin | Yêu cầu Claude mở rộng thêm 1-2 H2 bổ sung |
| Bài quá dài (trên 800 từ) | Sinh ra quá nhiều H2 hoặc đoạn quá dài | Yêu cầu Claude cắt bớt H2 hoặc rút gọn đoạn về 3-4 dòng |
| Anchor text không được chèn | Claude bỏ qua anchor text trong quá trình viết | Nhắc lại: "Chèn anchor text 1 vào H2 X và anchor text 2 vào H2 Y" |

---

## ĐỊNH DẠNG ĐẦU RA

Sau khi hoàn thành, in kết quả cho user:

```
✅ Đã viết bài SEO thành công!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Keyword     : [keyword]
📐 Độ dài      : ~[số] từ
📄 Google Docs : https://docs.google.com/document/d/xxx/edit
📊 Sheet hàng  : [row] — cột Google Docs URL đã cập nhật
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
