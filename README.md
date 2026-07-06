# Claude Code Skills — BTVN Buổi 3

Bộ 3 skills Claude Code được tạo cho bài tập về nhà buổi 3.

## Danh sách Skills

### 1. `/seo-content-writer`
Viết bài SEO 500–800 từ từ Google Sheets, tạo Google Docs và trả URL về sheet.

- **Kết nối ngoài:** Google Sheets API + Google Docs API + Google Drive API
- **Supporting files:** `scripts/sheets_handler.py`, `install.sh`, `requirements.txt`
- **Cách dùng:** `/seo-content-writer [số hàng]`

### 2. `/compare-content-seo-competitor`
So sánh nội dung SEO của brand với đối thủ TOP. Crawl URL, phân tích gap về heading, độ dài, format, LSI keyword, bigram và mật độ từ khoá.

- **Kết nối ngoài:** HTTP crawling (requests + BeautifulSoup4)
- **Supporting files:** `scripts/compare.py`, `install.sh`, `requirements.txt`
- **Cách dùng:** `/compare-content-seo-competitor <brand-url> <comp1-url> [comp2-url] ...`

### 3. `/duyet-bai-seo`
Duyệt bài viết SEO dựa trên outline có sẵn. Kiểm tra 4 tiêu chí: vị trí từ khoá, độ phủ outline, lỗi chính tả, hình ảnh và chú thích.

- **Kết nối ngoài:** Google Docs API
- **Supporting files:** `scripts/reader.py`, `install.sh`, `requirements.txt`
- **Cách dùng:** `/duyet-bai-seo <outline-url> <article-url> <keyword>`

---

## Cấu trúc thư mục

```
.claude/
└── skills/
    ├── seo-content-writer/
    │   ├── SKILL.md
    │   ├── install.sh
    │   ├── requirements.txt
    │   └── scripts/
    │       └── sheets_handler.py
    ├── compare-content-seo-competitor/
    │   ├── SKILL.md
    │   ├── install.sh
    │   ├── requirements.txt
    │   └── scripts/
    │       └── compare.py
    └── duyet-bai-seo/
        ├── SKILL.md
        ├── install.sh
        ├── requirements.txt
        └── scripts/
            └── reader.py
Output/
├── seo-content-writer.md
├── compare-content-seo-competitor.md
└── duyet-bai-seo.md
```

## Yêu cầu

- Claude Code CLI
- Python 3.10+ (khuyến nghị Python 3.13 từ python.org)
- `oauth_client.json` cho các skill dùng Google API (tự tạo tại GCP Console)

## Output

Thư mục `Output/` chứa kết quả thực chạy của từng skill.
