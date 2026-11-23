---
name: "viet-bai-seo-html-cms"
description: "Viết bài SEO hoàn chỉnh (3000-8000 từ) từ keyword + outline, ra mã HTML dán thẳng CMS, dùng lại ảnh bài cũ, kèm Title/Meta nghiên cứu TOP Google, giao trên trang có nút Copy."
---

# Viết bài SEO hoàn chỉnh → HTML cho CMS + trang Copy

**Yêu cầu Claude.ai (web/Cowork)** — skill dùng tính năng Project (`project_info`, hồ sơ `claude/project-<tên-website>.md`) và trình duyệt tích hợp (`Claude_Browser__preview_start`, `Claude_Browser__javascript_tool`) để kiểm tra ảnh. Các tool/tính năng này chưa có trong Claude Code CLI, nên Bước 1 (đọc hồ sơ Project) và Bước 4.2 (kiểm tra ảnh bằng trình duyệt) sẽ không chạy được ở đây; các bước còn lại (đọc outline qua Google Docs MCP, WebFetch/WebSearch, viết bài, xuất artifact) dùng được.

Đầu ra cuối cùng LUÔN là 1 trang artifact (công cụ copy) gồm 3 trường, mỗi trường có nút Copy:
1. **Title** (1 phương án chính + 2 phương án khác, bộ đếm ký tự, cảnh báo > 60).
2. **Meta description** (1 chính + 2 khác, cảnh báo > 160, mục thu gọn "Tham khảo TOP Google").
3. **Nội dung bài (HTML)** trong textarea monospace, hiện số từ + số ảnh.

KHÔNG giao file .html qua SendUserFile (mở ra thành trang xem trước, người dùng không copy được mã).

## Bước 0. Nhận đầu vào

Bắt buộc (thiếu thì hỏi 1 lần bằng AskUserQuestion, gom tất cả vào 1 câu hỏi):
- Từ khóa chính.
- Outline: link Google Docs hoặc dán trực tiếp.
- URL bài cũ trên website (để lấy lại ảnh). Nếu không có: dùng ảnh từ trang dịch vụ/bài liên quan cùng chủ đề trên website và nói rõ trong báo cáo.

Tùy chọn (mặc định nếu không nói):
- Website/khách hàng (suy từ outline hoặc hồ sơ dự án).
- Mẫu HTML của CMS: bắt buộc với website MỚI chưa có hồ sơ; website đã có hồ sơ thì dùng quy tắc HTML trong hồ sơ.
- Độ dài: 3000 - 8000 từ. Giọng văn: dễ hiểu cho người không có nền tảng chuyên môn, thông tin thuần SEO, không hoa mỹ, có luận điểm + ví dụ cụ thể.
- Định dạng: sapo và kết luận in nghiêng (<em>), trong sapo và kết luận CHỈ in đậm từ khóa chính.

## Bước 1. Đọc hồ sơ dự án

- Nếu session gắn Project: `project_info` rồi đọc `claude/project-<tên-website>.md` (hồ sơ: số liệu chuẩn, USP, CTA, hotline, từ cấm, đối thủ không được nhắc, quy tắc HTML, banner tái dùng, phản hồi cũ). Mọi quy tắc trong hồ sơ được ưu tiên hơn mặc định của skill.
- Chưa có hồ sơ: làm bài xong thì tạo hồ sơ mới (xem Bước 9).

## Bước 2. Đọc outline

- Google Docs: `mcp__Google_Docs__read_doc`. Kết quả thường quá lớn và bị lưu ra file JSON → trích bằng script python `-I` (duyệt `content.tabs[].documentTab.body.content`, in heading style, text, link, bảng dạng `a | b | c`). Đọc HẾT các tab: tab khác có thể chứa brief/mẫu HTML.
- Ghi lại: Title tag, Meta trong outline, H1, sapo định hướng, từng H2/H3 + định hướng + bảng + internal link + ghi chú "Chờ xác nhận".

## Bước 3. Nghiên cứu, kiểm chứng

- Thông tin dịch vụ (giá, thời gian, quy trình, giấy tờ): WebFetch các trang trên website khách. Đối chiếu số trong outline với website; chỗ nào lệch → dùng số ở mục chi tiết và liệt kê trong báo cáo.
- Thông tin ngoài (luật, quy định, số liệu y khoa): WebSearch kiểm chứng, ghi tên văn bản/điều khoản đúng; kiểm tra còn hiệu lực.
- Không bịa số. Thiếu thông tin → viết "liên hệ hotline để được báo giá/tư vấn" và báo người dùng.

## Bước 4. Lấy và kiểm tra ảnh

1. WebFetch URL bài cũ (và trang dịch vụ liên quan) với prompt: liệt kê mọi ảnh trong nội dung chính: src đầy đủ, alt, nằm dưới heading nào. Ảnh trong mẫu HTML người dùng dán cũng dùng được.
2. Container thường bị chặn mạng tới website khách; WebFetch đôi khi đọc SAI tên file ảnh. Vì vậy PHẢI kiểm tra từng URL bằng trình duyệt tích hợp:
   - `Claude_Browser__preview_start` mở 1 trang bất kỳ của website.
   - `Claude_Browser__javascript_tool` chạy fetch HEAD cho từng đường dẫn, thử các đuôi jpg/png/webp, chỉ nhận khi `ok` và content-type bắt đầu bằng `image`.
   - URL hỏng → đọc `img.currentSrc` trên trang cũ để lấy tên thật.
3. Ưu tiên file gốc .jpg/.png (không dùng bản .webp do plugin tối ưu ảnh sinh ra).
4. Phân bổ: 1 ảnh sau sapo, mỗi H2/H3 chính 1 ảnh phù hợp nội dung, banner hotline/Zalo sau phần ưu đãi và giữa bài, ảnh chuyên gia cuối bài. Alt tiếng Việt có dấu, chứa từ khóa khi tự nhiên; chú thích in nghiêng căn giữa.

## Bước 5. Viết bài (HTML)

- Bám đúng thứ tự, tên H2/H3 của outline. KHÔNG đưa H1 vào HTML (H1 là tiêu đề bài trong CMS). Bắt đầu bằng sapo.
- Mẫu mặc định (khi hồ sơ không quy định khác, theo chuẩn WordPress classic):
  - Đoạn văn: `<p style="text-align: justify;">...</p>`
  - Heading: `<h2><strong>...</strong></h2>`, `<h3><strong>...</strong></h3>`; anchor nội bộ thì thêm id vào thẻ h.
  - Danh sách: `<ul><li style="text-align: justify;">...</li></ul>`
  - Ảnh: `<p style="text-align: center;"><img class="aligncenter size-medium" src="..." alt="..." width=".." height=".." /></p>` + `<p style="text-align: center;"><em>chú thích</em></p>`
  - Bảng: `<table style="border-collapse: collapse; width: 100%;">`, hàng tiêu đề trong `<thead>` với `<td><strong>`. Mỗi thông tin 1 cột riêng (vd. dịch vụ, thời gian, giá tách cột).
  - Ưu đãi nổi bật: `<span style="color: #ff0000;">`; CTA cuối bài: `<blockquote>`.
  - Banner gọi điện bọc `<a href="tel:...">`, Zalo bọc `<a href="https://zalo.me/...">`.
- Nội dung: mỗi luận điểm có giải thích "vì sao" + ví dụ cụ thể (tính tiền, tình huống). Giải thích thuật ngữ bằng lời thường. Internal link theo outline, anchor tự nhiên. FAQ theo outline, trả lời trực tiếp ở câu đầu. Kết luận tóm tắt + thông điệp thương hiệu + CTA (hotline/địa chỉ theo hồ sơ).
- Viết theo từng phần (part1/part2/part3.html) rồi ghép, tránh 1 lần ghi quá dài.

## Bước 6. Kiểm tra bài (script python)

- Số từ (bỏ thẻ, unescape) trong khoảng yêu cầu.
- Từ cấm theo hồ sơ (vd. "chẩn đoán", "an toàn tuyệt đối", "có thể" khi nói về độ chính xác) = 0; in các câu chứa "có thể" để rà.
- Cân bằng thẻ HTML (HTMLParser, bỏ qua img/br).
- Sapo/kết luận: có <em>, chỉ <strong> quanh từ khóa chính.
- Mọi giá/số liệu khớp nguồn; phép tính trong ví dụ đúng.
- Mọi URL ảnh đã qua Bước 4.

## Bước 7. Title + Meta

- Lấy TOP Google: mở `https://www.google.com/search?q=<keyword>&hl=vi&gl=vn` bằng trình duyệt tích hợp, chạy JS lấy `#search a h3` (title, url, snippet) 5 kết quả đầu. (Ahrefs `serp-overview` country=vn có thể trả rỗng, chỉ dùng phụ.)
- Lấy title/meta thật của TOP 1-3: WebFetch; trang chặn thì mở bằng trình duyệt và đọc `document.title` + `meta[name=description]`.
- Rút ra pattern (con số giá/khoảng giá, "bao nhiêu tiền", "bảng giá", năm...). Viết 3 title (≤ 60 ký tự, từ khóa ở đầu) và 3 meta (140 - 160 ký tự, có từ khóa, con số/USP, lời kêu gọi). Phương án chính ưu tiên Title/Meta trong outline nếu đạt chuẩn. Không nhắc tên đối thủ bị cấm trong title/meta/bài; bảng tham khảo TOP trên trang công cụ thì được ghi tên miền.

## Bước 8. Dựng trang Copy, kiểm tra, publish

Tạo `config.json` {keyword, brand, date, titles[3], metas[3], serp:[[hạng, tên miền, title, nhận xét meta]], serp_note, body_path} rồi chạy script dưới (python3 build_page.py config.json out.html):

```python
import html,re,json,sys
c=json.load(open(sys.argv[1],encoding='utf-8'))
body=open(c['body_path'],encoding='utf-8').read().strip()+'\n'
words=len(html.unescape(re.sub(r'<[^>]+>',' ',body)).split())
def alts(k,lst):
  o=''
  for i,t in enumerate(lst[1:],2):
    o+=f'<div class="alt"><span class="alt-text" id="{k}{i}">{html.escape(t)}</span><span class="cnt">{len(t)} ký tự</span><button class="btn sm" data-copy="{k}{i}">Copy</button><button class="btn sm ghost" data-use="{k}{i}" data-target="{k}">Dùng làm chính</button></div>'
  return o
serp=''.join(f'<tr><td>{html.escape(str(a))}</td><td>{html.escape(b)}</td><td>{html.escape(t)}</td><td>{html.escape(n)}</td></tr>' for a,b,t,n in c['serp'])
T=html.escape(c['keyword'][:1].upper()+c['keyword'][1:])
page=f'''<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{T} – Bài SEO {html.escape(c['brand'])}</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#1d2430;--muted:#667085;--line:#e3e6eb;--acc:#0b6bcb;--ok:#14804a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:28px 20px 60px}}h1{{font-size:22px;margin:0 0 4px}}.sub{{color:var(--muted);margin:0 0 22px;font-size:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:18px}}
.head{{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}}.head h2{{font-size:16px;margin:0;flex:1}}
.cnt{{color:var(--muted);font-size:13px;white-space:nowrap}}.cnt.warn{{color:#b54708}}
.field{{width:100%;border:1px solid var(--line);border-radius:8px;padding:10px 12px;font:inherit;background:#fbfcfd;color:var(--ink);resize:vertical}}
textarea.code{{font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;height:520px;white-space:pre;overflow:auto}}
.btn{{border:0;background:var(--acc);color:#fff;border-radius:8px;padding:8px 16px;font:600 14px/1 inherit;cursor:pointer}}.btn.done{{background:var(--ok)}}
.btn.sm{{padding:6px 10px;font-size:12.5px}}.btn.ghost{{background:transparent;color:var(--acc);border:1px solid var(--acc)}}
.alts{{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px}}.lbl{{font-size:13px;color:var(--muted);margin-bottom:6px}}
.alt{{display:flex;align-items:center;gap:8px;padding:6px 0;flex-wrap:wrap}}.alt-text{{flex:1;min-width:220px;font-size:14px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}th,td{{border-bottom:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top}}th{{color:var(--muted)}}
details summary{{cursor:pointer;font-weight:600}}.note{{font-size:13px;color:var(--muted);margin:10px 0 0}}
</style></head><body><div class="wrap"><h1>{T}</h1>
<p class="sub">Bài SEO cho {html.escape(c['brand'])} · Từ khóa chính: {html.escape(c['keyword'])} · Cập nhật {html.escape(c['date'])}</p>
<section class="card"><div class="head"><h2>Title</h2><span class="cnt" id="cTitle"></span><button class="btn" data-copy="title">Copy</button></div>
<input class="field" id="title" value="{html.escape(c['titles'][0])}"><div class="alts"><div class="lbl">Phương án khác</div>{alts('title',c['titles'])}</div></section>
<section class="card"><div class="head"><h2>Meta description</h2><span class="cnt" id="cMeta"></span><button class="btn" data-copy="meta">Copy</button></div>
<textarea class="field" id="meta" rows="3">{html.escape(c['metas'][0])}</textarea><div class="alts"><div class="lbl">Phương án khác</div>{alts('meta',c['metas'])}</div>
<details style="margin-top:12px"><summary>Tham khảo TOP Google (gl=vn, {html.escape(c['date'])})</summary><table><thead><tr><th>#</th><th>Trang</th><th>Title</th><th>Điểm chính của meta</th></tr></thead><tbody>{serp}</tbody></table><p class="note">{html.escape(c['serp_note'])}</p></details></section>
<section class="card"><div class="head"><h2>Nội dung bài viết (HTML)</h2><span class="cnt">{words:,} từ · {body.count('<img')} ảnh</span><button class="btn" data-copy="content">Copy toàn bộ HTML</button></div>
<textarea class="field code" id="content" spellcheck="false" readonly>{html.escape(body)}</textarea>
<p class="note">Dán vào tab "Văn bản" (HTML) của trình soạn thảo, không dán vào tab "Trực quan". Ảnh dùng link gốc trên website nên sẽ hiện khi xem bài trên website.</p></section></div>
<script>
function countUpd(){{const t=title.value.length,m=meta.value.length;cTitle.textContent=t+' ký tự';cMeta.textContent=m+' ký tự';cTitle.className='cnt'+(t>60?' warn':'');cMeta.className='cnt'+(m>160?' warn':'');}}
title.addEventListener('input',countUpd);meta.addEventListener('input',countUpd);countUpd();
function getText(id){{const el=document.getElementById(id);return el.tagName==='SPAN'?el.textContent:el.value;}}
async function copyText(x){{try{{await navigator.clipboard.writeText(x);return true}}catch(e){{const ta=document.createElement('textarea');ta.value=x;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();let ok=false;try{{ok=document.execCommand('copy')}}catch(_){{}}ta.remove();return ok}}}}
document.addEventListener('click',async e=>{{const b=e.target.closest('button');if(!b)return;
if(b.dataset.copy){{const ok=await copyText(getText(b.dataset.copy));const o=b.textContent;b.textContent=ok?'Đã copy':'Chưa copy được, hãy chọn và Ctrl+C';b.classList.add('done');setTimeout(()=>{{b.textContent=o;b.classList.remove('done')}},1600);if(!ok){{const el=document.getElementById(b.dataset.copy);if(el.select)el.select();}}}}
if(b.dataset.use){{const s=document.getElementById(b.dataset.use),tg=document.getElementById(b.dataset.target);const old=tg.value;tg.value=s.textContent;s.textContent=old;s.nextElementSibling.textContent=old.length+' ký tự';countUpd();}}}});
</script></body></html>'''
open(sys.argv[2],'w',encoding='utf-8').write(page);print('words',words,'imgs',body.count('<img'))
```

Kiểm tra bằng Playwright (node, `require('playwright')`): mở file, xác nhận `#content.value === body`, cấp quyền clipboard, bấm "Copy toàn bộ HTML" và đọc lại clipboard khớp body, không có pageerror; chụp màn hình xem bố cục.

Publish: đọc `mcp__claude-artifacts__guide` topic pages (lần đầu trong session), rồi `publish_files` với files=[{as:"index.html", path:out.html}], title "<Keyword viết hoa chữ đầu> – Bài SEO <Brand>", icon "code". Sửa bài sau này: build lại và publish_files kèm slug + base_version.

## Bước 9. Lưu hồ sơ dự án + báo cáo

- Cập nhật (hoặc tạo) `claude/project-<website>.md`: quy tắc HTML của CMS, banner tái dùng, số liệu đã kiểm chứng, điểm lệch trên website, SERP tham khảo, dòng "Bài đã viết" (keyword, số từ, số ảnh, link artifact). Đọc toàn bộ hồ sơ rồi ghi lại đầy đủ (không có patch).
- Báo cáo người dùng ngắn gọn: link trang Copy; title/meta chính; số từ/ảnh; danh sách cần kiểm tra (số liệu lệch trên website, mục còn thiếu giá, ảnh thay thế nếu không có URL bài cũ).