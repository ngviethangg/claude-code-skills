---
name: "bao-cao-backlink-bao-guestpost"
description: "Tạo báo cáo index Google + ghi nhận Ahrefs cho link báo/guest post, xuất trang có bộ lọc và nút copy link lỗi. Dùng khi người dùng gửi danh sách link báo/guest post kèm domain website."
---

# Báo cáo index & backlink cho link báo / guest post

**Yêu cầu Claude.ai (web/Cowork)** — skill dùng `javascript_tool` để check index Google trực tiếp. Tool này chưa có trong Claude Code CLI, nên bước check index sẽ không chạy được ở đây cho tới khi có công cụ trình duyệt tương đương (phần check Ahrefs qua MCP và dựng báo cáo thì chạy bình thường).

**Đầu vào:** danh sách URL bài báo / guest post + domain website khách hàng.
**Đầu ra:** trang báo cáo (artifact) theo nhận diện SEONGON: KPI tổng quan, bảng trạng thái từng link, cột ghi chú lỗi, nút Copy link lỗi ở đầu bảng, bộ lọc Tất cả / Đang lỗi / Không lỗi, lọc theo loại lỗi, ô tìm kiếm.

Đã có đủ danh sách link + domain thì làm luôn, không hỏi thêm. Thiếu domain thì hỏi đúng 1 câu. Tên thương hiệu hiển thị: lấy từ title trang chủ website hoặc từ tên người dùng gọi; không rõ thì dùng domain.

Tạo task list: (1) Check index Google, (2) Kiểm tra trực tiếp trang bài viết, (3) Check Ahrefs, (4) Dựng & kiểm tra báo cáo, (5) Publish.

## Bước 1 – Chuẩn hoá đầu vào

- Bỏ dòng trống, URL trùng, khoảng trắng, tham số tracking (utm_*, fbclid...).
- SITE_HOST = domain website, bỏ giao thức, bỏ www., bỏ path (ví dụ https://danangthanhkhe.aeonmall-vietnam.com/vi → danangthanhkhe.aeonmall-vietnam.com).
- Dạng so khớp của mỗi URL: bỏ http(s)://, bỏ www., bỏ dấu / cuối.

## Bước 2 – Check index Google bằng site:url (trình duyệt tích hợp)

Dùng built-in browser (mcp__remote-devices__Claude_Browser__*; nạp tất cả bằng một lần ToolSearch). Không có thì dùng Claude in Chrome. Mở tab đầu bằng preview_start, các URL sau dùng browser_batch, mỗi batch 3–4 URL theo chuỗi: navigate → wait 3s → javascript_tool.

URL tìm kiếm: https://www.google.com/search?q=site%3A + URL đã bỏ giao thức (encode) + &hl=vi&gl=vn&pws=0

Đoạn JS đọc kết quả:

```js
({captcha: !!document.querySelector('#captcha-form, form[action*=sorry]') || location.href.includes('/sorry/'), noResult: /trong tài liệu nào|không khớp với bất kỳ tài liệu|did not match any documents/i.test(document.body.innerText), links: [...document.querySelectorAll('#search a:has(h3)')].map(a => a.href)})
```

- Có link trong `links` trùng URL (sau chuẩn hoá) → indexed = true.
- noResult = true, hoặc không có link trùng → indexed = false. Nếu links rỗng và noResult = false thì đọc lại bằng get_page_text để chắc chắn.
- captcha = true → dừng, nhờ người dùng giải CAPTCHA trong trình duyệt rồi chạy tiếp. Không giải được → indexed = null (Không xác định).
- Chỉ khi không có trình duyệt nào mới dùng WebSearch, và ghi chú kết quả index là tham khảo.

## Bước 3 – Kiểm tra trực tiếp trang bài viết

Mở từng URL bài viết (browser_batch: navigate → wait 3s → javascript_tool), thay SITE_HOST trong đoạn JS:

```js
(() => { const host = 'SITE_HOST'; const nav = performance.getEntriesByType('navigation')[0]; const as = [...document.querySelectorAll('a[href]')].filter(a => { try { const h = new URL(a.href).hostname.replace(/^www[.]/, ''); return h === host || h.endsWith('.' + host); } catch (e) { return false; } }); return { status: nav && nav.responseStatus, robots: document.querySelector('meta[name=robots]')?.content || '', canonical: document.querySelector('link[rel=canonical]')?.href || '', links: as.map(a => ({ a: a.innerText.trim().slice(0, 100), to: a.href, nofollow: /nofollow|sponsored|ugc/i.test(a.rel) })) }; })()
```

- Mã HTTP: lấy `status`; tab context cũng báo khi trang trả 404.
- `robots` chứa noindex → noindex = true. `canonical` khác URL bài (sau chuẩn hoá) → canonicalOther = true.
- Số link về web = số phần tử `links` (đây là số liệu gốc để xét lỗi Thiếu link).
- Trang không tải được (timeout, chặn bot) → links = null và lấy anchor từ kết quả Ahrefs ở bước 4 nếu có.

## Bước 4 – Check Ahrefs (gộp 1 request, tiết kiệm unit)

Mỗi request Ahrefs tốn tối thiểu khoảng 50 unit, nên gộp mọi URL vào 1 request (danh sách dài thì chia lô khoảng 25 URL). Không gọi lại Ahrefs cho cùng danh sách trong cùng phiên trừ khi người dùng yêu cầu.

Request chính – tool site-explorer-all-backlinks:
- target: SITE_HOST · mode: subdomains · aggregation: all · limit: 500
- history: since:(hôm nay trừ 90 ngày, YYYY-MM-DD) – tương đương chế độ Recent của Ahrefs
- select: url_from,url_to,anchor,is_dofollow,first_seen_link,last_visited,is_lost,lost_reason,domain_rating_source
- where: {'or':[{'field':'url_from_plain','is':['substring','<URL đã chuẩn hoá 1>']}, ...]} (JSON thật dùng nháy kép)

Request bổ sung (chỉ khi còn URL chưa khớp): target = root domain của website, history: all_time, where chỉ gồm các URL còn thiếu. Vẫn không có → ahrefs = 'no'.

Kết luận: có dòng khớp với is_lost = false → 'yes' (lấy first_seen_link, định dạng dd/mm/yyyy); chỉ có dòng is_lost = true → 'lost'; không có dòng nào → 'no'.

## Bước 5 – Quy tắc lỗi (template tự gắn nhãn từ dữ liệu)

| Lỗi | Điều kiện |
|---|---|
| Bài viết 404 / Lỗi HTTP xxx | http ≥ 400 |
| Chưa index | indexed = false |
| Trang noindex | robots có noindex |
| Canonical trỏ URL khác | canonical khác URL bài |
| Thiếu link (x/2) | số link về web < 2 (minLinks mặc định 2) |
| Có link nofollow | có link về web mang nofollow/sponsored/ugc |
| Ahrefs chưa ghi nhận | ahrefs = 'no' |
| Link đã mất | ahrefs = 'lost' |

Trường `extra` của mỗi dòng: 1–2 câu hướng xử lý, ví dụ: 404 → liên hệ báo khôi phục bài hoặc xin URL mới; 0 link → bài không chứa link về web, yêu cầu báo chèn link; thiếu link → yêu cầu bổ sung link; đã index nhưng Ahrefs chưa ghi nhận → đợi thêm hoặc đẩy link trỏ về bài để Ahrefs crawl; link trỏ trang chủ gốc thay vì trang ngôn ngữ (ví dụ / thay vì /vi) → ghi chú thêm.

## Bước 6 – Dựng báo cáo, kiểm tra, publish

1. Chép nguyên TEMPLATE bên dưới vào /home/claude/bao-cao-backlink-<domain>/index.html, chỉ thay 2 dòng CONFIG và DATA.
2. Định dạng DATA (mỗi URL một object, giữ thứ tự người dùng gửi):
   `{ url, http: 200|404|null, indexed: true|false|null, noindex: false, canonicalOther: false, ahrefs: 'yes'|'no'|'lost', firstSeen: 'dd/mm/yyyy'|null, links: [{ a: 'anchor', to: 'URL đích', nofollow: false }] | null, extra: 'ghi chú hướng xử lý' }`
3. Kiểm tra bằng Playwright (node, chromium.launch()): trang không có pageerror, số dòng bảng = số URL, bấm lọc Đang lỗi ra đúng số link lỗi, chụp ảnh toàn trang (deviceScaleFactor 1) và xem lại.
4. Publish bằng Artifact tool (mcp__claude-artifacts__publish_files) với title: Check index & backlink – <Tên thương hiệu>, icon: link. Không có Artifact tool thì gửi file bằng SendUserFile.
5. Trả lời ngắn: link báo cáo, 1 câu kết quả (x/n đã index, y/n Ahrefs ghi nhận, z link lỗi), bảng nhỏ liệt kê link lỗi + lỗi, số unit Ahrefs đã dùng.

## TEMPLATE

```html
<!DOCTYPE html>
<html lang='vi'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Check index & backlink</title>
<link href='https://fonts.googleapis.com/css2?family=Google+Sans:wght@400..700&family=Parkinsans:wght@400..800&display=swap' rel='stylesheet'>
<style>
:root { --sg-blue:#004AEF; --sg-green:#07EF9C; --sg-cyan:#0FD6F7; --sg-yellow:#FFCE00; --sg-blue-nhat:#E5EDFE; --sg-blue-nhat-2:#CCDBFC; --sg-green-nhat:#DFFDF1; --sg-cyan-nhat:#E2FAFE; --sg-yellow-nhat:#FFF6D6; --sg-chu:#434343; --sg-den:#1F1F1F; --sg-xam:#F3F3F3; --sg-vien:#CCDBFC; --sg-trang:#FFFFFF; --sg-gradient:linear-gradient(90deg,#004AEF 0%,#07EF9C 100%); --sg-font:'Google Sans',Arial,sans-serif; --sg-bo-goc:16px; }
* { box-sizing:border-box; }
body { margin:0; font-family:var(--sg-font); color:var(--sg-chu); background:var(--sg-trang); font-size:14px; }
a { color:var(--sg-blue); }
.wrap { max-width:1320px; margin:0 auto; padding:0 24px; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:18px 0; }
.logo { font-weight:700; font-size:20px; color:var(--sg-blue); letter-spacing:.5px; }
.tagline { font-size:12px; color:var(--sg-blue); }
.tagline b { color:var(--sg-den); background:var(--sg-green); padding:1px 6px; border-radius:4px; font-weight:600; }
.hero { background:var(--sg-gradient); color:var(--sg-trang); border-radius:var(--sg-bo-goc); padding:28px 32px; }
.hero h1 { margin:0 0 8px; font-size:26px; color:var(--sg-trang); }
.hero .meta { display:flex; flex-wrap:wrap; gap:8px 24px; font-size:13px; }
.hero .meta a { color:var(--sg-trang); }
.kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin:20px 0; }
.kpi { background:var(--sg-trang); border:1px solid var(--sg-vien); border-radius:var(--sg-bo-goc); padding:18px 20px; }
.kpi .lbl { font-size:12px; text-transform:uppercase; letter-spacing:.4px; }
.kpi .val { font-size:30px; font-weight:700; color:var(--sg-blue); margin-top:4px; }
.kpi .val small { font-size:15px; color:var(--sg-chu); font-weight:500; }
.kpi .bar { height:6px; background:var(--sg-xam); border-radius:99px; margin-top:10px; overflow:hidden; }
.kpi .bar i { display:block; height:100%; background:var(--sg-blue); border-radius:99px; }
.kpi.warn { background:var(--sg-yellow-nhat); border-color:var(--sg-yellow); }
.kpi.warn .val { color:var(--sg-den); }
.toolbar { display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between; margin:8px 0 12px; }
.left, .right { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.seg { display:inline-flex; background:var(--sg-xam); border-radius:999px; padding:4px; }
.seg button { border:0; background:transparent; font-family:var(--sg-font); font-size:13px; font-weight:600; color:var(--sg-chu); padding:8px 16px; border-radius:999px; cursor:pointer; }
.seg button.on { background:var(--sg-blue); color:var(--sg-trang); }
.seg button .c { opacity:.75; font-weight:500; margin-left:4px; }
select, input[type=search] { font-family:var(--sg-font); font-size:13px; color:var(--sg-den); border:1px solid var(--sg-vien); border-radius:999px; padding:9px 14px; background:var(--sg-trang); outline:none; }
input[type=search] { min-width:220px; }
select:focus, input:focus { border-color:var(--sg-blue); }
.btn { border:0; border-radius:999px; padding:10px 18px; font-family:var(--sg-font); font-weight:600; font-size:13px; cursor:pointer; display:inline-flex; gap:8px; align-items:center; }
.btn-cta { background:var(--sg-yellow); color:var(--sg-den); }
.btn-cta:disabled { opacity:.45; cursor:not-allowed; }
.btn-ghost { background:var(--sg-blue-nhat); color:var(--sg-blue); }
.tbl-wrap { border:1px solid var(--sg-vien); border-radius:var(--sg-bo-goc); overflow:auto; }
table { width:100%; border-collapse:collapse; min-width:1100px; }
thead th { background:var(--sg-blue); color:var(--sg-trang); text-align:left; font-weight:600; font-size:12.5px; padding:12px; white-space:nowrap; position:sticky; top:0; }
tbody td { padding:12px; vertical-align:top; border-top:1px solid var(--sg-xam); font-size:13px; }
tbody tr:nth-child(even) td { background:var(--sg-xam); }
tbody tr.err td:first-child { box-shadow:inset 4px 0 0 var(--sg-yellow); }
td.num { text-align:center; color:var(--sg-den); font-weight:600; }
.url a { text-decoration:none; word-break:break-all; font-weight:500; }
.url a:hover { text-decoration:underline; }
.url .dom { display:block; font-size:11.5px; margin-bottom:2px; text-transform:uppercase; letter-spacing:.3px; }
.pill { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; white-space:nowrap; }
.ok { background:var(--sg-green-nhat); color:var(--sg-den); border:1px solid var(--sg-green); }
.no { background:var(--sg-yellow-nhat); color:var(--sg-den); border:1px solid var(--sg-yellow); }
.idk { background:var(--sg-xam); color:var(--sg-chu); border:1px solid var(--sg-vien); }
.st-err { background:var(--sg-yellow); color:var(--sg-den); }
.st-ok { background:var(--sg-green); color:var(--sg-den); }
.cnt { font-weight:700; color:var(--sg-den); }
.cnt.low { background:var(--sg-yellow-nhat); padding:2px 8px; border-radius:6px; }
.anchors { margin:0; padding:0; list-style:none; }
.anchors li { margin-bottom:6px; line-height:1.4; }
.anchors .a { color:var(--sg-den); font-weight:600; }
.anchors .to { font-size:12px; word-break:break-all; }
.tag { display:inline-block; background:var(--sg-yellow-nhat); border:1px solid var(--sg-yellow); color:var(--sg-den); font-size:11.5px; font-weight:600; padding:2px 8px; border-radius:6px; margin:0 4px 4px 0; }
.note { font-size:12.5px; line-height:1.45; margin-top:2px; }
.note.fine { color:var(--sg-den); }
.empty { text-align:center; padding:40px; }
.rules { margin:20px 0; background:var(--sg-blue-nhat); border-radius:var(--sg-bo-goc); padding:16px 20px; font-size:13px; }
.rules h3 { margin:0 0 8px; font-size:14px; color:var(--sg-blue); }
.rules ul { margin:0; padding-left:18px; line-height:1.6; }
.footer { margin-top:24px; background:var(--sg-blue); color:var(--sg-trang); display:flex; justify-content:space-between; font-size:12px; }
.footer .l { padding:12px 24px; }
.footer .r { background:var(--sg-green); color:var(--sg-den); font-weight:700; padding:12px 28px 12px 40px; clip-path:polygon(24px 0,100% 0,100% 100%,0 100%); }
.toast { position:fixed; left:50%; bottom:28px; transform:translateX(-50%) translateY(20px); background:var(--sg-den); color:var(--sg-trang); padding:12px 20px; border-radius:999px; font-size:13px; opacity:0; transition:.25s; pointer-events:none; z-index:10; }
.toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
.toast b { color:var(--sg-green); }
.modal-bg { position:fixed; inset:0; background:rgba(31,31,31,.45); display:none; align-items:center; justify-content:center; z-index:9; }
.modal-bg.show { display:flex; }
.modal { background:var(--sg-trang); border-radius:var(--sg-bo-goc); padding:20px; width:min(720px,92vw); }
.modal h3 { margin:0 0 8px; color:var(--sg-blue); }
.modal textarea { width:100%; height:200px; font-family:var(--sg-font); font-size:12.5px; border:1px solid var(--sg-vien); border-radius:10px; padding:10px; }
.modal .act { display:flex; justify-content:flex-end; margin-top:10px; }
@media (max-width:860px) { .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); } .hero h1 { font-size:21px; } }
</style>
</head>
<body>
<div class='wrap'>
  <div class='topbar'><div class='logo'>SEONGON</div><div class='tagline'><b>AI-First</b> ↗ Search Marketing Growth Partner</div></div>
  <section class='hero'>
    <h1 id='h1'></h1>
    <div class='meta'><span>Website: <a id='siteLink'></a></span><span>Ngày check: <span id='checkDate'></span></span><span>Nguồn: Google <code>site:url</code> · Kiểm tra trực tiếp trang · Ahrefs Backlinks</span></div>
  </section>
  <section class='kpis' id='kpis'></section>
  <div class='toolbar'>
    <div class='left'>
      <button class='btn btn-cta' id='copyBtn' title='Copy URL các bài đang lỗi theo bộ lọc hiện tại'>⧉ Copy link lỗi <span id='copyCount'></span></button>
      <div class='seg' id='seg'>
        <button data-f='all' class='on'>Tất cả<span class='c' id='cAll'></span></button>
        <button data-f='err'>Đang lỗi<span class='c' id='cErr'></span></button>
        <button data-f='ok'>Không lỗi<span class='c' id='cOk'></span></button>
      </div>
    </div>
    <div class='right'>
      <select id='typeSel'></select>
      <input type='search' id='q' placeholder='Tìm theo URL, báo, anchor…'>
    </div>
  </div>
  <div class='tbl-wrap'>
    <table>
      <thead><tr><th>#</th><th>URL bài viết</th><th>Trạng thái</th><th>Index Google</th><th>Ahrefs</th><th>Link về web</th><th>Ngày Ahrefs thấy</th><th>Anchor → trang đích</th><th>Ghi chú lỗi</th></tr></thead>
      <tbody id='tb'></tbody>
    </table>
  </div>
  <div class='rules'>
    <h3>Quy tắc đánh giá lỗi</h3>
    <ul>
      <li><b>Bài viết 404 / Lỗi HTTP</b>: URL trả mã lỗi (bài bị gỡ hoặc đổi đường dẫn).</li>
      <li><b>Chưa index</b>: lệnh <code>site:url</code> trên Google không trả về đúng URL bài viết.</li>
      <li><b>Trang noindex / Canonical trỏ URL khác</b>: bài chặn Google index hoặc khai báo canonical sang URL khác.</li>
      <li><b>Thiếu link</b>: bài có ít hơn <b id='minL'></b> link trỏ về website.</li>
      <li><b>Có link nofollow</b>: link về website mang thuộc tính nofollow / sponsored / ugc.</li>
      <li><b>Ahrefs chưa ghi nhận</b>: URL bài không có trong báo cáo Backlinks của Ahrefs cho website.</li>
      <li><b>Link đã mất</b>: Ahrefs từng ghi nhận nhưng link đã bị gỡ.</li>
    </ul>
  </div>
</div>
<div class='footer'><div class='l' id='foot'></div><div class='r'>SEONGON</div></div>
<div class='toast' id='toast'></div>
<div class='modal-bg' id='modalBg'><div class='modal'><h3>Danh sách link lỗi</h3><div class='note'>Trình duyệt chặn copy tự động – bấm Ctrl/Cmd + C để copy phần đã chọn.</div><textarea id='fallbackTa' readonly></textarea><div class='act'><button class='btn btn-ghost' id='closeModal'>Đóng</button></div></div></div>
<script>
const CONFIG = { site: 'example.com', siteUrl: 'https://example.com', brand: 'Tên website', date: 'dd/mm/yyyy', minLinks: 2 }; // THAY DÒNG NÀY
const DATA = []; // THAY DÒNG NÀY

const MIN_LINKS = CONFIG.minLinks || 2;
const $ = id => document.getElementById(id);
const esc = s => { const d = document.createElement('div'); d.textContent = String(s); return d.innerHTML.replace(/'/g, '&#39;'); };
const path = u => { try { const x = new URL(u); return x.pathname + x.search; } catch (e) { return u; } };
document.title = 'Check index & backlink – ' + CONFIG.brand;
$('h1').textContent = 'Check index & backlink – ' + CONFIG.brand;
$('siteLink').href = CONFIG.siteUrl; $('siteLink').textContent = CONFIG.site;
$('checkDate').textContent = CONFIG.date;
$('foot').textContent = '↗ Báo cáo check index & backlink · ' + CONFIG.brand;

function errorsOf(r) {
  const e = []; const bad = r.http && r.http >= 400;
  if (bad) e.push(r.http === 404 ? 'Bài viết 404' : 'Lỗi HTTP ' + r.http);
  if (r.indexed === false) e.push('Chưa index');
  if (r.noindex) e.push('Trang noindex');
  if (r.canonicalOther) e.push('Canonical trỏ URL khác');
  if (!bad && Array.isArray(r.links) && r.links.length < MIN_LINKS) e.push('Thiếu link (' + r.links.length + '/' + MIN_LINKS + ')');
  if (Array.isArray(r.links) && r.links.some(l => l.nofollow)) e.push('Có link nofollow');
  if (r.ahrefs === 'no') e.push('Ahrefs chưa ghi nhận');
  if (r.ahrefs === 'lost') e.push('Link đã mất');
  return e;
}
const typeKey = t => t.startsWith('Thiếu link') ? 'Thiếu link' : t.startsWith('Lỗi HTTP') ? 'Lỗi HTTP' : t;
DATA.forEach((r, i) => { r.i = i + 1; r.errs = errorsOf(r); try { r.dom = new URL(r.url).hostname.replace(/^www[.]/, ''); } catch (e) { r.dom = ''; } });

const state = { f: 'all', type: '', q: '' };
function visible() {
  const q = state.q.trim().toLowerCase();
  return DATA.filter(r => {
    if (state.f === 'err' && !r.errs.length) return false;
    if (state.f === 'ok' && r.errs.length) return false;
    if (state.type && !r.errs.some(t => typeKey(t) === state.type)) return false;
    if (q) { const hay = (r.url + ' ' + (r.links || []).map(l => l.a + ' ' + l.to).join(' ') + ' ' + r.errs.join(' ')).toLowerCase(); if (!hay.includes(q)) return false; }
    return true;
  });
}
function renderKpis() {
  const n = DATA.length, idx = DATA.filter(r => r.indexed === true).length, ah = DATA.filter(r => r.ahrefs === 'yes').length, er = DATA.filter(r => r.errs.length).length;
  const k = (lbl, v, tot, cls) => `<div class='kpi ${cls || ''}'><div class='lbl'>${lbl}</div><div class='val'>${v}${tot ? `<small> / ${tot} · ${Math.round(v / tot * 100)}%</small>` : ''}</div>${tot ? `<div class='bar'><i style='width:${v / tot * 100}%'></i></div>` : ''}</div>`;
  $('kpis').innerHTML = k('Tổng link', n) + k('Đã index Google', idx, n) + k('Ahrefs đã ghi nhận', ah, n) + k('Link đang lỗi', er, n, er ? 'warn' : '');
  $('cAll').textContent = n; $('cErr').textContent = er; $('cOk').textContent = n - er; $('minL').textContent = MIN_LINKS;
  const types = [...new Set(DATA.flatMap(r => r.errs.map(typeKey)))];
  $('typeSel').innerHTML = `<option value=''>Mọi loại lỗi</option>` + types.map(t => `<option value='${esc(t)}'>${esc(t)} (${DATA.filter(r => r.errs.some(x => typeKey(x) === t)).length})</option>`).join('');
}
function renderTable() {
  const rows = visible(); const errRows = rows.filter(r => r.errs.length);
  $('copyCount').textContent = '(' + errRows.length + ')'; $('copyBtn').disabled = !errRows.length;
  if (!rows.length) { $('tb').innerHTML = `<tr><td colspan='9' class='empty'>Không có link nào khớp bộ lọc.</td></tr>`; return; }
  $('tb').innerHTML = rows.map(r => {
    const bad = r.http && r.http >= 400;
    const cnt = bad || !Array.isArray(r.links) ? '–' : `<span class='cnt ${r.links.length < MIN_LINKS ? 'low' : ''}'>${r.links.length}/${MIN_LINKS}</span>`;
    const anchors = r.links && r.links.length ? `<ul class='anchors'>${r.links.map(l => `<li><span class='a'>${esc(l.a || '(không có anchor text)')}</span>${l.nofollow ? ' <span class=tag>nofollow</span>' : ''}<br><span class='to'>→ ${esc(path(l.to))}</span></li>`).join('')}</ul>` : `<span class='note'>—</span>`;
    const notes = r.errs.length ? r.errs.map(t => `<span class='tag'>${esc(t)}</span>`).join('') + (r.extra ? `<div class='note'>${esc(r.extra)}</div>` : '') : `<div class='note fine'>${esc(r.extra || ('Đủ ' + (r.links ? r.links.length : '') + ' link, đã index & Ahrefs đã ghi nhận.'))}</div>`;
    const ix = r.indexed === true ? ['ok', 'Đã index'] : r.indexed === false ? ['no', 'Chưa index'] : ['idk', 'Không xác định'];
    const ah = r.ahrefs === 'yes' ? ['ok', 'Đã ghi nhận'] : r.ahrefs === 'lost' ? ['no', 'Link đã mất'] : ['no', 'Chưa ghi nhận'];
    return `<tr class='${r.errs.length ? 'err' : ''}'><td class='num'>${r.i}</td><td class='url'><span class='dom'>${esc(r.dom)}</span><a href='${esc(r.url)}' target='_blank' rel='noopener'>${esc(r.url.replace(/^https?:[/][/](www[.])?/, ''))}</a></td><td><span class='pill ${r.errs.length ? 'st-err' : 'st-ok'}'>${r.errs.length ? 'Lỗi' : 'OK'}</span></td><td><span class='pill ${ix[0]}'>${ix[1]}</span></td><td><span class='pill ${ah[0]}'>${ah[1]}</span></td><td class='num'>${cnt}</td><td>${r.firstSeen || '—'}</td><td>${anchors}</td><td>${notes}</td></tr>`;
  }).join('');
}
function toast(html) { const t = $('toast'); t.innerHTML = html; t.classList.add('show'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 2200); }
async function copyErrors() {
  const list = visible().filter(r => r.errs.length).map(r => r.url); if (!list.length) return;
  const text = list.join(String.fromCharCode(10)); let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) {}
  if (!ok) { try { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); ok = document.execCommand('copy'); ta.remove(); } catch (e) {} }
  if (ok) toast('Đã copy <b>' + list.length + '</b> link lỗi'); else { $('fallbackTa').value = text; $('modalBg').classList.add('show'); $('fallbackTa').select(); }
}
const setSeg = f => { state.f = f; document.querySelectorAll('#seg button').forEach(x => x.classList.toggle('on', x.dataset.f === f)); };
$('seg').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; setSeg(b.dataset.f); renderTable(); });
$('typeSel').addEventListener('change', e => { state.type = e.target.value; if (state.type && state.f === 'ok') setSeg('err'); renderTable(); });
$('q').addEventListener('input', e => { state.q = e.target.value; renderTable(); });
$('copyBtn').addEventListener('click', copyErrors);
$('closeModal').addEventListener('click', () => $('modalBg').classList.remove('show'));
$('modalBg').addEventListener('click', e => { if (e.target === $('modalBg')) $('modalBg').classList.remove('show'); });
renderKpis(); renderTable();
</script>
</body>
</html>
```

## Lưu ý

- Màu và font theo nhận diện SEONGON 7.2026: lỗi/cảnh báo dùng Yellow, không dùng đỏ; chữ tiếng Việt dùng Google Sans. Không đổi màu trong template.
- Số link về web lấy từ kiểm tra trực tiếp trang (bước 3); Ahrefs chỉ dùng để xác định đã ghi nhận hay chưa và ngày thấy link.
- Khi người dùng yêu cầu chạy lại với danh sách mới, tạo artifact mới; nếu họ muốn cập nhật báo cáo cũ thì republish vào slug cũ.