# Claude Code Skills

Bộ skills Claude Code cá nhân (bắt đầu từ bài tập về nhà buổi 3, bổ sung dần về sau).

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

### 4. `/cro-report`
Tạo báo cáo hiệu quả SEO & Chuyển đổi hàng tháng (GA4 + Search Console + CRO engine + Ahrefs, thêm CRM nếu có). Kiểm tra site đã đủ sự kiện CRO chưa, thu thập số liệu, viết nhận định, xuất HTML artifact rồi PDF.

- **Kết nối ngoài:** GA4 Data/Admin API, Search Console API, Google Sheets API (qua skill `seo-analyst`), Ahrefs (MCP tool), Chrome headless (xuất PDF)
- **⚠️ Phụ thuộc bắt buộc:** skill **`seo-analyst`** phải được cài và cấu hình trước — `cro-report` dùng chung virtualenv Python + token OAuth theo từng site của skill đó. `seo-analyst` **chưa có trong repo này**, cần skill đó riêng.
- **Supporting files:** `scripts/{preflight,collect,build,crm,render,export_pdf,common}.py`, `assets/`, `profiles/_template.json`, `install.sh`
- **Cách dùng:** `/cro-report` (chọn hồ sơ website có sẵn hoặc tạo mới)
- **Lưu ý dữ liệu:** `profiles/*.json` (trừ `_template.json`) và `reports/` chứa thông tin định danh + số liệu thật của khách hàng — bị `.gitignore` chặn, không commit.

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
    ├── duyet-bai-seo/
    │   ├── SKILL.md
    │   ├── install.sh
    │   ├── requirements.txt
    │   └── scripts/
    │       └── reader.py
    └── cro-report/
        ├── SKILL.md
        ├── install.sh
        ├── assets/
        ├── profiles/_template.json
        └── scripts/
            └── {preflight,collect,build,crm,render,export_pdf,common}.py
Output/
├── seo-content-writer.md
├── compare-content-seo-competitor.md
└── duyet-bai-seo.md
```

## Yêu cầu

- Claude Code CLI
- Python 3.10+ (khuyến nghị Python 3.13 từ python.org)
- `oauth_client.json` cho các skill dùng Google API (tự tạo tại GCP Console)
- `/cro-report` cần cài thêm skill `seo-analyst` (chưa có trong repo này) trước khi dùng

## Output

Thư mục `Output/` chứa kết quả thực chạy của từng skill.
