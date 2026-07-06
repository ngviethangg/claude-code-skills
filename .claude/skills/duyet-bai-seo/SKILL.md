---
name: duyet-bai-seo
description: Duyệt nội dung bài viết SEO dựa trên outline có sẵn. Nhận URL outline (Google Docs) + URL bài viết hoàn chỉnh (Google Docs) + từ khoá chính. Kiểm tra 4 tiêu chí: (1) vị trí & tần suất từ khoá, (2) các phần outline đã triển khai hay chưa, (3) lỗi chính tả, (4) hình ảnh và chú thích. Dùng khi user gõ "duyệt bài SEO", "review bài viết", "check bài SEO", hoặc "/duyet-bai-seo".
when_to_use: |
  Trigger phrases: "duyệt bài SEO", "review bài viết SEO", "check bài viết",
  "kiểm tra bài SEO", "duyệt content", "đối chiếu outline", "/duyet-bai-seo"
user-invokable: true
argument-hint: "<outline-url> <article-url> <keyword>"
allowed-tools: Bash Read Write
metadata:
  author: nguyenviethangg
  version: "1.0.0"
  category: seo
---

# /duyet-bai-seo — SEO Content Reviewer

Duyệt bài viết SEO dựa trên outline đã có, kiểm tra từ khoá, độ phủ outline, lỗi chính tả và hình ảnh. **Yêu cầu Claude Code** — không hoạt động trong Claude.ai web chat.

---

## BƯỚC 0 — Bootstrap (chạy tự động lần đầu)

Kiểm tra Python venv:

```bash
test -f ~/.claude/skills/duyet-bai-seo/.venv/bin/python && echo "READY" || echo "NEED_SETUP"
```

Nếu `NEED_SETUP`:

```bash
bash ~/.claude/skills/duyet-bai-seo/install.sh 2>&1 | tail -15
```

---

## BƯỚC 1 — Nhận đầu vào

Nếu user chạy `/duyet-bai-seo <outline-url> <article-url> <keyword>` → dùng từ argument.

Nếu không có argument, hỏi user:

> **URL Google Docs chứa OUTLINE** (1 URL):
> **URL Google Docs chứa BÀI VIẾT HOÀN CHỈNH** (1 URL):
> **Từ khoá chính** (1 cụm từ, vd: "xe máy điện cho học sinh"):

Lưu vào:
- `OUTLINE_URL` — URL của tài liệu outline
- `ARTICLE_URL` — URL của bài viết hoàn chỉnh
- `KEYWORD` — từ khoá chính cần kiểm tra

---

## BƯỚC 2 — Đọc cả hai tài liệu

Lưu keyword vào file tạm để dùng ở bước sau:

```bash
echo "$KEYWORD" > /tmp/seo_review_kw.txt
```

Đọc outline:

```bash
~/.claude/skills/duyet-bai-seo/.venv/bin/python \
  ~/.claude/skills/duyet-bai-seo/scripts/reader.py \
  read "$OUTLINE_URL" > /tmp/seo_outline.json 2>/tmp/seo_outline_err.txt
cat /tmp/seo_outline_err.txt >&2
```

Đọc bài viết:

```bash
~/.claude/skills/duyet-bai-seo/.venv/bin/python \
  ~/.claude/skills/duyet-bai-seo/scripts/reader.py \
  read "$ARTICLE_URL" > /tmp/seo_article.json 2>/tmp/seo_article_err.txt
cat /tmp/seo_article_err.txt >&2
```

Đọc nội dung JSON:

```bash
cat /tmp/seo_outline.json
cat /tmp/seo_article.json
```

Nếu file JSON trống hoặc có `error`, báo cáo lỗi cụ thể và dừng.

---

## BƯỚC 3 — Đếm tần suất từ khoá

Đếm số lần từ khoá xuất hiện trong bài viết (không phân biệt hoa/thường):

```bash
~/.claude/skills/duyet-bai-seo/.venv/bin/python3 - << 'PYEOF'
import json
kw = open('/tmp/seo_review_kw.txt').read().strip().lower()
data = json.load(open('/tmp/seo_article.json'))
text = data['full_text'].lower()
count = text.count(kw)
print(f'{count}')
PYEOF
```

Lưu kết quả này để dùng trong báo cáo mục 4.1.

---

## BƯỚC 4 — Phân tích và xuất báo cáo

Dựa trên dữ liệu JSON từ outline và bài viết, thực hiện **4 kiểm tra** sau:

---

### 4.1 Kiểm tra từ khoá chính

Dùng `KEYWORD` (từ đầu vào), `doc_title`, `sapo`, `conclusion`, `headings`, `full_text` từ JSON bài viết.

Hiển thị bảng:

| Vị trí | Có từ khoá? | Nội dung |
|--------|-------------|----------|
| Tiêu đề bài (doc_title) | ✅ / ❌ | [nội dung tiêu đề] |
| Sapo (đoạn đầu) | ✅ / ❌ | [50 ký tự đầu của sapo] |
| Kết bài | ✅ / ❌ | [50 ký tự đầu của conclusion] |
| Tần suất trong bài | **X lần** | [số đếm từ BƯỚC 3] |

Tiếp theo, liệt kê **các heading chứa từ khoá**:

```
Heading có từ khoá:
  • H2: [heading text] ✅
  • H3: [heading text] ✅
  • ... (hoặc "Không có heading nào chứa từ khoá" nếu rỗng)
```

**Đánh giá chung:** Từ khoá đã đủ vị trí quan trọng chưa? Nếu thiếu vị trí nào, ghi chú cụ thể.

---

### 4.2 Đối chiếu Outline

So sánh danh sách `headings` trong JSON outline vs `headings` trong JSON bài viết.

Với mỗi heading trong outline, tìm heading tương đương trong bài viết (so sánh ngữ nghĩa, không cần khớp 100% từ ngữ):

| Phần trong Outline | Trạng thái | Ghi chú |
|--------------------|-----------|---------|
| H2: [text] | ✅ Đã triển khai | Bài: "[matched heading]" |
| H3: [text] | ✅ Đã triển khai | Bài: "[matched heading]" |
| H2: [text] | ❌ Chưa có | Không tìm thấy mục tương đương |
| H3: [text] | ⚠️ Gần đúng | Bài có "[closest]" nhưng nội dung khác |

Sau bảng, liệt kê rõ:

```
❌ Các phần outline CHƯA được triển khai:
  1. [heading text] (level H?)
  2. [heading text] (level H?)
  (hoặc "✅ Tất cả phần outline đã được triển khai")
```

---

### 4.3 Kiểm tra lỗi chính tả

Đọc `full_text` từ JSON bài viết, tìm lỗi chính tả tiếng Việt:
- Sai dấu thanh điệu (huyền/sắc/hỏi/ngã/nặng dùng nhầm chỗ)
- Sai phụ âm đầu thường gặp: d/gi/r, x/s, ch/tr, n/ng
- Thiếu/thừa âm cuối
- Lỗi gõ tắt hoặc gõ không dấu
- Từ tiếng Anh sai chính tả

Hiển thị bảng lỗi phát hiện được:

| # | Từ sai trong bài | Sửa thành | Ngữ cảnh (đoạn chứa lỗi) |
|---|-----------------|-----------|--------------------------|
| 1 | "..." | "..." | "...[context]..." |
| 2 | "..." | "..." | "...[context]..." |

Nếu không phát hiện lỗi: `✅ Không phát hiện lỗi chính tả rõ ràng.`

> **Lưu ý:** Tập trung vào lỗi rõ ràng, không đánh dấu lỗi với tên riêng, thương hiệu, hoặc từ chuyên ngành có chủ đích.

---

### 4.4 Kiểm tra hình ảnh

Dùng `image_count` và `images` array từ JSON bài viết.

Hiển thị tổng quan:

```
Tổng số hình ảnh: X ảnh
```

Hiển thị bảng chi tiết:

| # | Có chú thích? | Nội dung chú thích | Alt text? |
|---|--------------|-------------------|-----------|
| 1 | ✅ | "[caption text]" | ✅ / ❌ |
| 2 | ❌ | — | ❌ |

Nếu `image_count = 0`:

```
⚠️ Bài viết chưa có hình ảnh nào. Nên bổ sung ảnh minh hoạ để tăng UX và SEO.
```

**Đánh giá:** Tỷ lệ ảnh có chú thích là X/Y. Liệt kê số thứ tự ảnh còn thiếu chú thích.

---

## BƯỚC 5 — Tổng kết

Sau 4 tiêu chí, xuất bảng tổng kết:

```
📊 KẾT QUẢ DUYỆT BÀI
─────────────────────────────────────────────────────
Tiêu chí                    | Kết quả     | Ghi chú
─────────────────────────────────────────────────────
1. Từ khoá chính            | ✅/⚠️/❌    | [ngắn gọn]
2. Độ phủ outline           | ✅/⚠️/❌    | X/Y mục đã triển khai
3. Lỗi chính tả             | ✅/⚠️/❌    | Phát hiện X lỗi
4. Hình ảnh & chú thích     | ✅/⚠️/❌    | X/Y ảnh có chú thích
─────────────────────────────────────────────────────
📋 CẦN SỬA TRƯỚC KHI ĐĂNG:
  🔴 [vấn đề nghiêm trọng cần fix ngay nếu có]
  🟡 [vấn đề nên sửa]
  🟢 [gợi ý cải thiện nếu có]
─────────────────────────────────────────────────────
```

---

## TIÊU CHÍ CHẤT LƯỢNG

Báo cáo đạt yêu cầu khi:

- [ ] Đọc thành công cả outline và bài viết (không có lỗi JSON)
- [ ] Bảng 4.1 đủ 4 vị trí (title, sapo, kết bài, tần suất) + danh sách heading
- [ ] Bảng 4.2 liệt kê tất cả heading trong outline và trạng thái của từng mục
- [ ] Mục 4.3 xác nhận rõ ràng có/không có lỗi chính tả
- [ ] Mục 4.4 báo cáo đúng số lượng ảnh và tỷ lệ có chú thích
- [ ] Bảng tổng kết BƯỚC 5 có đủ 4 dòng

---

## LỖI THƯỜNG GẶP

### Lỗi xác thực OAuth

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `oauth_client.json not found` | Chưa có credentials | Đặt file tại `~/.claude/skills/duyet-bai-seo/oauth_client.json` hoặc copy từ `seo-content-writer` |
| `403 access_denied` | Email chưa trong Test Users | GCP → OAuth consent screen → Test users → Add email |
| `Token expired / invalid_grant` | Token hết hạn | Xóa `credentials/token.json` rồi chạy lại |
| `403 Forbidden` từ Docs API | Chưa enable Google Docs API | GCP Console → Enable "Google Docs API" |

### Lỗi đọc tài liệu

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `Không tìm được Document ID` | URL sai định dạng | Đảm bảo URL dạng `docs.google.com/document/d/ID/edit` |
| JSON trống hoặc `doc_title` rỗng | Tài liệu không tồn tại hoặc chưa được chia sẻ | Kiểm tra quyền truy cập tài liệu (Share → Anyone with link) |
| `headings` trả về `[]` | Tài liệu không dùng heading style | Trong Google Docs, dùng Format → Paragraph styles → Heading 2/3 thay vì in đậm |
| `sapo` rỗng | Đoạn đầu quá ngắn (< 20 ký tự) | Kiểm tra tài liệu có nội dung không |

### Lỗi phân tích

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `image_count` = 0 dù bài có ảnh | Ảnh dán vào dạng Drawing, không phải Inline image | Google Docs Drawing không được đếm; chỉ Insert → Image mới nhận diện được |
| `conclusion` bị rỗng | Bài không có heading "kết" và không có đoạn cuối rõ ràng | Xem lại cấu trúc tài liệu; đảm bảo có ≥ 1 đoạn văn NORMAL_TEXT ở cuối |
| Tần suất đếm ra 0 dù bài có keyword | Keyword có dấu thanh điệu khác nhau | Kiểm tra lại keyword nhập vào có đúng dấu không |

### Lỗi môi trường

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `ModuleNotFoundError: googleapiclient` | Chưa cài dependencies | Chạy lại `bash install.sh` |
| `NEED_SETUP` mỗi lần | Venv bị xóa | Chạy `bash install.sh` để tạo lại |
| `ensurepip returned non-zero exit status 1` | Python 3.14 từ Homebrew bị lỗi | Dùng Python 3.13 từ python.org; `install.sh` đã tự chọn đúng |

---

## ĐỊNH DẠNG ĐẦU RA

```
✅ BÁO CÁO DUYỆT BÀI SEO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Từ khoá : [keyword]
📋 Outline : [outline_url]
📄 Bài viết: [article_url]  ([word_count] từ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1️⃣  Từ khoá chính
[bảng + danh sách heading]

## 2️⃣  Đối chiếu Outline
[bảng + danh sách thiếu]

## 3️⃣  Lỗi chính tả
[bảng lỗi hoặc thông báo không có lỗi]

## 4️⃣  Hình ảnh & Chú thích
[tổng số + bảng chi tiết]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 KẾT QUẢ DUYỆT BÀI
[bảng tổng kết + danh sách cần sửa]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
