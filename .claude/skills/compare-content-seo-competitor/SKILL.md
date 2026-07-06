---
name: compare-content-seo-competitor
description: So sánh nội dung SEO giữa bài viết của brand và các đối thủ TOP. Crawl URL brand + URLs đối thủ, phân tích: heading/section còn thiếu, độ dài bài, định dạng thiếu (bảng, bullet, FAQ...), LSI keyword chưa có, mật độ từ khoá lặp lại ở đối thủ. Dùng khi user nhắc "so sánh content", "compare content đối thủ", "gap content SEO", "thiếu gì so với đối thủ", hoặc "/compare-content-seo-competitor".
when_to_use: |
  Trigger phrases: "so sánh content SEO", "compare content đối thủ", "phân tích content đối thủ",
  "gap content", "thiếu gì so với đối thủ", "đối chiếu bài viết", "/compare-content-seo-competitor"
user-invokable: true
argument-hint: "<brand-url> <competitor-url-1> [competitor-url-2] ..."
allowed-tools: Bash Read Write
metadata:
  author: nguyenviethangg
  version: "1.0.0"
  category: seo
---

# /compare-content-seo-competitor — SEO Content Gap Analyzer

So sánh bài viết SEO của brand với các đối thủ TOP, tìm ra những gì brand đang thiếu. **Yêu cầu Claude Code** — không hoạt động trong Claude.ai web chat.

---

## BƯỚC 0 — Bootstrap (chạy tự động lần đầu)

Kiểm tra Python venv:

```bash
test -f ~/.claude/skills/compare-content-seo-competitor/.venv/bin/python && echo "READY" || echo "NEED_SETUP"
```

Nếu `NEED_SETUP`:

```bash
bash ~/.claude/skills/compare-content-seo-competitor/install.sh 2>&1 | tail -10
```

---

## BƯỚC 1 — Nhận URL đầu vào

Nếu user chạy `/compare-content-seo-competitor <brand-url> <comp1> <comp2>...` → dùng URL từ argument.

Nếu không có argument, hỏi user:

> **URL bài viết của brand** (1 URL):
> **URL các đối thủ** (tối thiểu 1, tối đa 5, cách nhau bằng dấu cách hoặc xuống dòng):

Lưu vào biến:
- `BRAND_URL` — 1 URL duy nhất
- `COMPETITOR_URLS` — danh sách 1–5 URL

---

## BƯỚC 2 — Crawl tất cả URL

Crawl brand URL trước:

```bash
~/.claude/skills/compare-content-seo-competitor/.venv/bin/python \
  ~/.claude/skills/compare-content-seo-competitor/scripts/compare.py \
  crawl "$BRAND_URL" > /tmp/seo_brand.json
```

Crawl tất cả competitor URL cùng lúc:

```bash
~/.claude/skills/compare-content-seo-competitor/.venv/bin/python \
  ~/.claude/skills/compare-content-seo-competitor/scripts/compare.py \
  crawl $COMPETITOR_URLS > /tmp/seo_competitors.json
```

Đọc kết quả:

```bash
cat /tmp/seo_brand.json
cat /tmp/seo_competitors.json
```

Nếu crawl bị lỗi (trường `error` có trong JSON), thông báo cho user URL nào không đọc được và tiếp tục với các URL còn lại. Cần ít nhất 1 đối thủ crawl thành công để tiếp tục.

---

## BƯỚC 3 — Phân tích và xuất báo cáo

Dựa trên dữ liệu JSON đã crawl, thực hiện **6 phân tích** theo thứ tự:

### 3.1 Heading / Section còn thiếu

So sánh danh sách `headings` (level 2 và 3) của brand với từng đối thủ.

Tìm heading xuất hiện ở **từ 2 bài đối thủ trở lên** nhưng KHÔNG có (hoặc tương tự) trong bài brand.

Hiển thị dạng bảng:

| Heading đang thiếu | Xuất hiện ở đối thủ | Gợi ý vị trí chèn |
|-------------------|---------------------|-------------------|
| ... | domain1.com, domain2.com | Sau H2 "..." |

### 3.2 So sánh độ dài bài viết

Hiển thị bảng so sánh `word_count`:

| Nguồn | Domain | Số từ | So với brand |
|-------|--------|-------|-------------|
| Brand | ... | ... | — |
| Đối thủ 1 | ... | ... | +/- X từ |
| Đối thủ 2 | ... | ... | +/- X từ |
| Trung bình đối thủ | — | ... | +/- X từ |

Kết luận: Brand cần bổ sung khoảng X từ để đạt mức trung bình.

### 3.3 Định dạng brand đang thiếu

So sánh các field `has_table`, `has_ol`, `has_ul`, `has_blockquote`, `has_faq`, `has_conclusion`, `has_table_of_contents`.

Liệt kê định dạng có ở **≥2 đối thủ** nhưng brand chưa dùng:

| Định dạng còn thiếu | Đối thủ đang dùng | Gợi ý áp dụng |
|---------------------|-------------------|---------------|
| Bảng (table) | domain1.com, domain2.com | So sánh thông số / tính năng |
| FAQ / Hỏi đáp | ... | Cuối bài, 3–5 câu hỏi thường gặp |

### 3.4 LSI Keyword brand cần bổ sung

Gộp tất cả `top_words` từ các đối thủ, tính tổng tần suất. Loại trừ những từ đã có trong `top_words` của brand (tần suất ≥ 2).

Hiển thị top 20 LSI keyword brand nên thêm vào bài:

| # | LSI Keyword | Tần suất ở đối thủ | Gợi ý chèn vào |
|---|-------------|-------------------|----------------|
| 1 | ... | X/Y bài | Heading / đoạn ... |

### 3.5 Cụm từ khoá (Bigram) brand chưa đề cập

Tương tự 3.4 nhưng với `top_bigrams` (cụm 2 từ). Hiển thị top 15 bigram:

| # | Cụm từ khoá | Tần suất ở đối thủ | Ngữ cảnh điển hình |
|---|------------|-------------------|--------------------|
| 1 | ... | X/Y bài | "..." |

### 3.6 Mật độ từ khoá chính

Lấy H1 của brand làm từ khoá chính. Tính tần suất xuất hiện (%) trong bài brand và trong từng bài đối thủ. Đánh giá brand đang over/under-optimize.

---

## BƯỚC 4 — Tóm tắt ưu tiên hành động

Sau 6 phân tích, liệt kê **Top 5 việc cần làm ngay** theo mức độ ưu tiên (impact cao → thấp):

```
📋 TOP 5 VIỆC CẦN LÀM NGAY
─────────────────────────────────────────────
🔴 [Cao] Thêm X từ để đạt độ dài trung bình đối thủ
🔴 [Cao] Bổ sung mục: "..." (có ở 3/3 đối thủ)
🟡 [Trung] Thêm bảng so sánh tại mục "..."
🟡 [Trung] Chèn LSI keyword: ..., ..., ...
🟢 [Thấp] Thêm mục FAQ với 3–5 câu hỏi thường gặp
─────────────────────────────────────────────
```

---

## TIÊU CHÍ CHẤT LƯỢNG

Phân tích đạt yêu cầu khi:

- [ ] Crawl thành công ≥1 URL brand và ≥1 URL đối thủ
- [ ] Báo cáo đủ cả 6 mục phân tích (3.1 → 3.6)
- [ ] Heading thiếu được đánh giá theo ngưỡng ≥2 đối thủ (không phải chỉ 1)
- [ ] LSI keyword và bigram đã loại trừ từ brand đã có
- [ ] Top 5 hành động được sắp xếp theo mức độ ưu tiên thực tế

---

## LỖI THƯỜNG GẶP

### Lỗi crawl

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `ConnectionError` / `Timeout` | Trang chặn bot hoặc quá chậm | Tăng timeout: sửa `timeout=30` trong script; thử lại 1 lần |
| `403 Forbidden` khi crawl | Trang chặn User-Agent | Thêm header Referer hoặc dùng URL khác của đối thủ |
| `SSLError` | Chứng chỉ SSL hết hạn hoặc không hợp lệ | Thêm `verify=False` vào `requests.get` (chỉ dùng tạm) |
| Nội dung crawl bị rỗng (`word_count` < 50) | Trang render bằng JavaScript | Ghi chú cho user: trang này dùng JS rendering, cần dùng Selenium để crawl chính xác |
| Encoding lỗi (ký tự bị vỡ) | Trang dùng encoding không chuẩn | Sửa thủ công: `resp.encoding = 'utf-8'` trong script |

### Lỗi phân tích

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| Không tìm được heading nào | Trang dùng thẻ div thay H2/H3 | Bổ sung selector CSS vào script cho trang cụ thể |
| LSI keyword toàn là từ vô nghĩa | Stopword list thiếu từ ngành | Thêm từ vào `VI_STOPWORDS` trong `compare.py` |
| `top_words` trả về toàn số hoặc ký tự đặc biệt | Regex chưa lọc hết | Tăng `len(w) >= 4` thay vì 3 trong `extract_words()` |

### Lỗi môi trường

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| `ModuleNotFoundError: beautifulsoup4` | Chưa cài dependencies | Chạy lại `bash install.sh` |
| `lxml not found` | lxml chưa được cài | `.venv/bin/pip install lxml` |
| `NEED_SETUP` mỗi lần chạy | Venv bị xóa hoặc ở sai đường dẫn | Chạy lại `bash install.sh` để tạo lại venv |

---

## ĐỊNH DẠNG ĐẦU RA

```
🔍 SEO CONTENT GAP ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Brand   : [domain]  ([X] từ)
🏆 Đối thủ : [domain1], [domain2], [domain3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[6 mục phân tích]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 TOP 5 VIỆC CẦN LÀM NGAY
[danh sách ưu tiên]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
