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

### 5. `/viet-bai-seo-html-cms`
Viết bài SEO hoàn chỉnh (3000–8000 từ) từ keyword + outline, xuất ra mã HTML dán thẳng vào CMS, dùng lại ảnh bài cũ, kèm Title/Meta nghiên cứu TOP Google. Giao trên 1 trang artifact có nút Copy riêng cho từng trường.

- **Kết nối ngoài:** Google Docs (đọc outline), WebFetch/WebSearch (nghiên cứu, lấy ảnh bài cũ)
- **Supporting files:** chỉ `SKILL.md` (không script/dependency)
- **Cách dùng:** `/viet-bai-seo-html-cms` (nêu từ khoá + outline + URL bài cũ)
- **⚠️ Giới hạn trong Claude Code:** skill viết cho Claude.ai/Cowork — phần đọc hồ sơ Project (`project_info`) và kiểm tra ảnh bằng trình duyệt tích hợp (`Claude_Browser__javascript_tool`/`preview_start`) không chạy được trong Claude Code CLI; phần đọc outline/viết bài/xuất artifact vẫn dùng được.

### 6. `/check-top-tu-khoa`
Check thứ hạng Google thực tế (phiên chưa đăng nhập, google.com.vn, top 20) cho danh sách từ khoá của một website, cập nhật trang theo dõi có ô tick, nút Check lại, nút Copy.

- **Kết nối ngoài:** Google Search (qua trình duyệt tích hợp của Cowork)
- **Supporting files:** chỉ `SKILL.md`
- **Cách dùng:** `/check-top-tu-khoa` (gửi danh sách từ khoá + domain)
- **⚠️ Giới hạn trong Claude Code:** dùng `tabs_context_mcp` + `javascript_tool` (chỉ có trên Claude.ai/Cowork) để đọc kết quả Google thật — **không chạy được trong Claude Code CLI** cho tới khi có công cụ trình duyệt tương đương.

### 7. `/bao-cao-backlink-bao-guestpost`
Tạo báo cáo index Google + ghi nhận Ahrefs cho link báo/guest post, xuất trang có bộ lọc và nút copy link lỗi.

- **Kết nối ngoài:** Google Search (check index), Ahrefs (MCP tool)
- **Supporting files:** chỉ `SKILL.md`
- **Cách dùng:** `/bao-cao-backlink-bao-guestpost` (gửi danh sách link + domain)
- **⚠️ Giới hạn trong Claude Code:** bước check index dùng `javascript_tool` (chỉ có trên Claude.ai/Cowork) — không chạy được ở đây; phần check Ahrefs qua MCP và dựng báo cáo vẫn dùng được.

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
    ├── cro-report/
    │   ├── SKILL.md
    │   ├── install.sh
    │   ├── assets/
    │   ├── profiles/_template.json
    │   └── scripts/
    │       └── {preflight,collect,build,crm,render,export_pdf,common}.py
    ├── viet-bai-seo-html-cms/
    │   └── SKILL.md
    ├── check-top-tu-khoa/
    │   └── SKILL.md
    └── bao-cao-backlink-bao-guestpost/
        └── SKILL.md
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
