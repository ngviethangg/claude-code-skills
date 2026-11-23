---
name: "check-top-tu-khoa"
description: "Check thứ hạng Google thực tế (phiên chưa đăng nhập, google.com.vn, top 20) cho từ khoá của một website và cập nhật trang theo dõi SEONGON có ô tick, nút Check lại, nút Copy."
---

# Check top từ khoá thực tế + trang theo dõi thứ hạng

**Yêu cầu Claude.ai (web/Cowork)** — skill dùng `tabs_context_mcp` + `javascript_tool` để mở tab và đọc kết quả Google thật. Hai tool này chưa có trong Claude Code CLI, nên phần check SERP sẽ không chạy được ở đây cho tới khi có công cụ trình duyệt tương đương.

Dùng khi người dùng gửi danh sách từ khoá của một website và muốn check thứ hạng, hoặc nhắn "check lại", "check top <domain>". Kết quả luôn nằm trên **một trang theo dõi riêng cho mỗi website** (artifact). Không tạo file CSV hay Drive, trừ khi người dùng xin.

## Quy ước đã thống nhất với người dùng

- **Độ sâu:** top 20 (2 trang Google). Không thấy website trong 20 kết quả thì ghi **"Ngoài top 20"**.
- **Thị trường:** google.com.vn, `hl=vi`, `gl=vn`, `pws=0`, máy tính, theo IP máy người dùng, **phiên chưa đăng nhập**.
- **Cách đếm vị trí:** chỉ tính kết quả web tự nhiên, tức các thẻ `#rso a h3`. Bỏ qua quảng cáo, AI Overview, "Mọi người cũng hỏi", hình ảnh. Bài Facebook hay diễn đàn nằm trong kết quả web vẫn được tính một vị trí.
- **Trạng thái mỗi từ khoá:**
  - `error` = "Lỗi check – cần check lại": bị chặn hoặc không đọc được kết quả.
  - `warn` = "Biến động – nên check lại": lần trước ở top 10 nay ra ngoài top 20, hoặc tụt từ 5 bậc trở lên.
  - `ok` cho các trường hợp còn lại.
- **Lịch sử:** chỉ giữ lần hiện tại và lần trước (`prev`).
- **Giao diện:** nhận diện SEONGON. Cột theo thứ tự: ô tick, #, Từ khoá, TOP hiện tại, TOP lần trước, URL ranking, Trạng thái. Không thêm cột khác. Chỉ người dùng xem, không cần tính năng chia sẻ.
- **Nút Copy** copy Từ khoá, TOP hiện tại, URL ranking dạng TSV.

## Giới hạn phải nói rõ với người dùng

- Cần tiện ích **Claude trên Chrome** đang kết nối (`mcp__claude-in-chrome__*`). Không có thì báo và dừng.
- Không mở được cửa sổ ẩn danh thật vì tiện ích chỉ điều khiển cửa sổ thường. Mỗi lượt tìm chạy trong một iframe `credentialless` (không cookie, không tài khoản) phủ toàn màn hình. Người dùng sẽ thấy trang Google có nút "Đăng nhập", không có avatar. Nói ngắn gọn điều này ngay lần đầu.
- Google có thể bật CAPTCHA. Claude **không tự giải**, mà nhờ người dùng tích "Tôi không phải người máy" trong khung đang hiện trên tab Chrome.
- Tốc độ khoảng 10–20 giây mỗi từ khoá.

## Quy trình

### 0. Tìm trang theo dõi của website

Gọi `mcp__claude-artifacts__list_artifacts` với `query` = `Theo dõi thứ hạng từ khoá – <domain>`.

- **Có trang:** đọc `ranking/current` bằng `db_get` để lấy cấu hình (domain, includeSubdomains, depth) và danh sách từ khoá cũ.
  - Trang tạo trước khi có skill (tài liệu chưa có trường `depth`): publish lại Template HTML lên chính trang đó (`publish_files` kèm `slug` và `base_version`) rồi mới ghi dữ liệu mới, trong đó có `depth: 20`.
- **Chưa có (lần đầu với website này):** hỏi người dùng những gì còn thiếu, và chỉ hỏi những gì chưa có:
  - domain;
  - danh sách từ khoá;
  - có tính cả subdomain không (mặc định: có; `www` luôn được tính).
- Danh sách có từ khoá trùng thì gộp lại, giữ thứ tự xuất hiện đầu tiên, và báo số dòng đã gộp.

### 1. Chạy check trên Chrome

1. `tabs_context_mcp` với `createIfEmpty: true`, rồi `navigate` tab đó tới `https://www.google.com/?hl=vi`.
2. Chạy **Script A** (bên dưới) bằng `javascript_tool`. Trước khi chạy, sửa `CFG` gồm `domain`, `includeSub`, `depth: 20` và `keywords`, rồi dùng `JSON.stringify` danh sách từ khoá để không lỗi dấu nháy.
   - Lần chạy mới hoàn toàn: trước đó chạy `sessionStorage.removeItem('R:' + '<domain>')`.
   - Check lại một số từ khoá: chỉ đưa các từ khoá đó vào `keywords`, và cũng xoá key trên.
3. Gửi người dùng một câu bằng `SendUserMessage`: đã mở phiên chưa đăng nhập trên tab Chrome của Claude, đang chạy N từ khoá, khoảng bao nhiêu phút, và đừng tải lại hay đóng tab đó.
4. Theo dõi tiến độ: mỗi lần gọi `javascript_tool` với `await new Promise(r=>setTimeout(r,29000)); ({...st, n:Object.keys(R).length})`. Không chờ quá 30 giây mỗi lần, vì công cụ có giới hạn thời gian.
   - `st.captcha === true`: gọi `SendUserMessage` nhờ người dùng tích ô "Tôi không phải người máy" trong khung Google trên tab Chrome. Vòng chạy tự đợi tối đa 10 phút.
   - `st.err === 'captcha'`: các từ khoá chưa check được ghi trạng thái `error`.
   - `st.err` bắt đầu bằng `'not logged out'`: dừng, báo người dùng, không ghi kết quả.
   - **Không gọi `runLoop` lần thứ hai khi vòng cũ còn chạy**, vì sẽ thành 2 vòng song song và Google chặn nhanh hơn. Muốn chạy lại thì tăng `window.gen` bằng cách chạy lại Script A, vì dòng `gen` sẽ vô hiệu vòng cũ.
5. Lấy kết quả gọn để tránh output bị cắt:
   - `window.T=[...new Set(Object.values(R).map(r=>r[1]).filter(Boolean))]`
   - `CFG.keywords.map((k,i)=>i+'|'+(R[k]?R[k][0]:'x')+'|'+(R[k]?T.indexOf(R[k][1]):-1)+'|'+(R[k]?R[k][3]:'error')).join(' ')`
   - Thêm danh sách `T` (tiêu đề) kèm `cite`.
6. Kiểm tra chéo: nếu một từ khoá thương hiệu hoặc từ khoá vốn ở top 1–3 nay "Ngoài top 20", chạy lại `anonSerp(kw,0)` cho từ khoá đó và xem danh sách `cite` để chắc không phải lỗi đọc.
7. Xong thì đóng tab bằng `tabs_close_mcp`.

### 2. Đổi tiêu đề trên Google thành URL thật

Link kết quả của phiên chưa đăng nhập là `/goto?...` và không đọc được URL gốc, nên phải đối chiếu theo tiêu đề:

1. Mở thêm một tab Chrome (`tabs_create_mcp`) tới `https://<domain>/` và chạy **Script B**.
2. Gọi lại `({tdone, n:Object.keys(titles).length})` cho đến khi `tdone` là `true`.
3. Chạy `mapTitles([...các tiêu đề...])`.
   - Có `url` thì dùng.
   - Nhiều ứng viên thì chọn trang không redirect hoặc theo canonical.
   - Không khớp (Google viết lại tiêu đề) thì để `url` rỗng và ghi `note` dạng "Không xác định được URL chính xác (Google hiển thị: <cite>)". Không đoán URL.

### 3. Ghi kết quả vào trang

Tài liệu `ranking/current` có dạng:

```json
{"domain":"example.vn","includeSubdomains":true,"depth":20,
 "method":"Google.com.vn, tiếng Việt, máy tính, phiên chưa đăng nhập (tương đương ẩn danh), check đến top 20",
 "checkedAt":"YYYY-MM-DD","prevCheckedAt":"YYYY-MM-DD",
 "rows":[{"kw":"...","pos":3,"url":"https://...","prev":1,"status":"ok","note":""}]}
```

- `pos` / `prev` là số, hoặc `null` nếu ngoài top 20. `prev` là `null` nếu chưa có lần trước.
- **Check toàn bộ:** `prev` của mỗi từ khoá = `pos` cũ, và `prevCheckedAt` = `checkedAt` cũ. Từ khoá mới thì `prev = null`. Từ khoá người dùng đã bỏ khỏi danh sách thì xoá khỏi `rows`.
- **Check lại vài từ khoá** (từ yêu cầu trong trang): chỉ cập nhật `pos`, `url`, `status`, `note` của các dòng đó. Giữ nguyên `prev` và `checkedAt`.
  - Nếu kết quả xác nhận một dòng đang `warn` hoặc `error`, đặt `status: "ok"` và ghi `note` "Đã check lại DD/MM: xác nhận".
- **Tính trạng thái:**
  - lỗi check → `error`, note "Không đọc được kết quả / bị Google chặn";
  - `prev ≤ 10` và `pos = null` → `warn`, note "Lần trước (DD/MM) TOP X, nay ngoài top 20.";
  - cả hai là số và `pos − prev ≥ 5` → `warn`, note "Giảm N bậc so với DD/MM (TOP X).";
  - còn lại → `ok`.
- Ghi bằng `mcp__claude-artifacts__db_write`: op `set` lên `ranking/current`. Tài liệu đã tồn tại thì cần `ifVersion` lấy từ `db_get`.

### 4. Tạo trang lần đầu cho website mới

1. Lấy **Template HTML** bên dưới, thay mọi `__DOMAIN__` bằng domain, ghi ra file `index.html` trong thư mục làm việc.
2. `mcp__claude-artifacts__publish_files` với `files: [{as:"index.html", path:<đường dẫn>}]`, `title: "Theo dõi thứ hạng từ khoá – <domain>"`, `icon: "chart"`.
3. `mcp__claude-artifacts__declare_capabilities` với `{"db":{"rules":[{"path":"","read":"view","write":"interact"}]},"user":{}}` và `base_version` lấy từ kết quả publish.
4. `db_write` tài liệu `ranking/current` như mục 3. Với lần đầu: `prev = null` và không có `prevCheckedAt`.
- Không đổi bố cục, màu hay cột của template, trừ khi người dùng yêu cầu.

### 5. Khi người dùng nhắn "check lại"

1. Tìm trang theo dõi (bước 0). Nếu có nhiều website và người dùng không nói rõ website nào, kiểm tra trang nào có yêu cầu đang chờ.
2. `db_query` collection `requests` với `where: {"status":"pending"}`.
   - Không có yêu cầu nào thì hỏi người dùng muốn check lại toàn bộ hay những từ khoá nào.
3. Đánh dấu mỗi yêu cầu `status: "running"` (op `update`, kèm `ifVersion`).
4. Gộp các từ khoá trong các yêu cầu, rồi chạy bước 1 → 2 → 3 theo kiểu "Check lại vài từ khoá".
5. Đánh dấu yêu cầu `status: "done"` và `doneAt` (ISO).

### 6. Báo kết quả

- Trả lời ngắn: đã check bao nhiêu từ khoá, số lượng mỗi nhóm (TOP 1 / 2–3 / 4–10 / 11–20 / Ngoài top 20), số từ khoá `warn` / `error`, các thay đổi đáng chú ý, rồi gửi link trang.
- **Không** dán lại toàn bộ bảng vào chat, trừ khi người dùng xin.
- Nếu thứ hạng giảm hàng loạt, kiểm tra nhanh website có cho phép index không: trạng thái 200, thẻ meta robots, canonical, robots.txt. Nêu kết quả và gợi ý xem Google Search Console.

## Script A – chạy check (trên tab Google)

```js
// === Dán vào tab Google (https://www.google.com/?hl=vi) bằng javascript_tool. Sửa CFG trước khi chạy. ===
window.CFG = { domain: 'example.vn', includeSub: true, depth: 20, keywords: [/* 'từ khoá 1', 'từ khoá 2' */] };
window.hostOf = c => { const m = (c || '').trim().match(/^(?:https?:\/\/)?([a-z0-9.-]+\.[a-z]{2,})(?:[\s›/]|$)/i); return m ? m[1].toLowerCase() : ''; };
window.isMine = c => { const h = hostOf(c).replace(/^www\./, ''); const d = CFG.domain.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, ''); return !!h && (h === d || (CFG.includeSub && h.endsWith('.' + d))); };
window.cur = null;
// Mỗi lượt tìm chạy trong iframe credentialless (không cookie, không tài khoản) phủ toàn màn hình để người dùng thấy trạng thái "Đăng nhập".
window.anonSerp = (q, start) => new Promise(res => {
  const f = document.createElement('iframe'); f.setAttribute('credentialless', '');
  f.style.cssText = 'width:100vw;height:100vh;position:fixed;left:0;top:0;z-index:2147483646;background:#fff;border:0';
  f.src = '/search?q=' + encodeURIComponent(q) + '&hl=vi&gl=vn&pws=0&start=' + (start || 0);
  let t = 0, last = -1, stable = 0;
  const chk = () => {
    t++; const d = f.contentDocument; const hs = d ? d.querySelectorAll('#rso a h3') : [];
    if (hs.length > 0 && hs.length === last) stable++; else stable = 0; last = hs.length;
    const txt = (d && d.body && d.body.innerText || '').slice(0, 3000);
    const blocked = /unusual traffic|không phải là người máy|lưu lượng truy cập bất thường/i.test(txt);
    if (stable >= 4 || t > 40 || blocked) {
      const out = []; hs.forEach(h => { const a = h.closest('a'); const blk = a.closest('.MjjYud') || a.closest('[data-hveid]') || a.parentElement; const c = blk.querySelector('cite'); out.push({ title: h.innerText, cite: c ? c.innerText : '' }); });
      if (window.cur && window.cur !== f) window.cur.remove(); window.cur = f;
      res({ blocked, loggedOut: !!d && /Đăng nhập/.test(txt.slice(0, 400)) && !d.querySelector('a[aria-label*="Tài khoản Google"],a[aria-label*="Google Account"]'), n: out.length, items: out });
    } else setTimeout(chk, 500);
  };
  f.onload = () => setTimeout(chk, 1500); document.body.appendChild(f);
});
// R[kw] = [pos|null, title, cite, 'ok'|'error'];  st = trạng thái vòng chạy
window.R = JSON.parse(sessionStorage.getItem('R:' + CFG.domain) || '{}'); window.st = { done: false, captcha: false, err: null }; window.lg = [];
window.gen = (window.gen || 0) + 1;
window.runLoop = async g => {
  const sl = ms => new Promise(r => setTimeout(r, ms)); st.done = false;
  const pages = Math.ceil(CFG.depth / 10);
  for (const k of CFG.keywords) {
    if (g !== window.gen) return; if (R[k]) continue;
    let pos = null, title = '', cite = '', off = 0, status = 'ok';
    for (let p = 0; p < pages; p++) {
      let r = await anonSerp(k, p * 10); lg.push([k, p, r.n, r.loggedOut, r.blocked]);
      if (r.blocked) { // chờ 90s rồi thử lại; nếu vẫn bị chặn: bật cờ captcha, chờ người dùng giải tối đa 10 phút
        await sl(90000); r = await anonSerp(k, p * 10);
        let waited = 0; while (r.blocked && waited < 600000) { st.captcha = true; await sl(15000); waited += 15000; r = await anonSerp(k, p * 10); }
        st.captcha = false; if (r.blocked) { st.err = 'captcha'; break; }
      }
      if (r.n === 0) { await sl(5000); r = await anonSerp(k, p * 10); if (r.n === 0) { status = 'error'; break; } }
      if (!r.loggedOut) { st.err = 'not logged out at ' + k; break; }
      const i = r.items.findIndex(x => isMine(x.cite));
      if (i >= 0) { pos = off + i + 1; title = r.items[i].title; cite = r.items[i].cite; break; }
      off += r.items.length; await sl(5000 + Math.random() * 4000);
    }
    if (st.err) break;
    if (typeof pos === 'number' && pos > CFG.depth) { pos = null; title = ''; cite = ''; }
    R[k] = [pos, title, cite, status]; sessionStorage.setItem('R:' + CFG.domain, JSON.stringify(R));
    await sl(5000 + Math.random() * 4000);
  }
  st.done = true;
};
runLoop(window.gen); ({ total: CFG.keywords.length, have: Object.keys(R).length });
```

## Script B – gom tiêu đề trang để đổi sang URL (trên tab của website)

```js
// === Chạy trong một tab Chrome đang mở trang chủ website (cùng origin) để đổi tiêu đề trên Google -> URL thật. ===
// Bước 1: gom URL từ sitemap rồi lấy <title> của từng trang (chạy nền, gọi lại để xem tiến độ).
window.collect = async () => {
  const seen = new Set(), pages = [];
  const grab = async u => { try { const r = await fetch(u); if (!r.ok) return ''; return await r.text(); } catch (e) { return ''; } };
  let roots = [];
  const robots = await grab('/robots.txt'); roots.push(...[...robots.matchAll(/^sitemap:\s*(\S+)/gim)].map(m => m[1]));
  roots.push(location.origin + '/sitemap_index.xml', location.origin + '/sitemap.xml', location.origin + '/wp-sitemap.xml');
  const queue = [...new Set(roots)];
  while (queue.length && seen.size < 60) {
    const sm = queue.shift(); if (seen.has(sm)) continue; seen.add(sm);
    const t = await grab(sm.replace(/^https?:\/\/[^/]+/, '')); if (!t) continue;
    const locs = [...t.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)].map(m => m[1].replace(/&amp;/g, '&'));
    if (/<sitemapindex/i.test(t)) queue.push(...locs); else pages.push(...locs.filter(u => !/\.(jpe?g|png|webp|gif|svg|pdf)$/i.test(u)));
  }
  window.urls = [...new Set([location.origin + '/', ...pages])].slice(0, 2000);
  window.titles = {}; window.tdone = false;
  (async () => {
    for (let i = 0; i < urls.length; i += 10) await Promise.all(urls.slice(i, i + 10).map(async u => {
      try { const r = await fetch(u.replace(/^https?:\/\/[^/]+/, '')); const h = await r.text();
        titles[u] = { title: (h.match(/<title[^>]*>([^<]*)<\/title>/i) || [])[1] || '', redirected: r.redirected, final: r.url,
          canon: (h.match(/rel=["']canonical["'][^>]*href=["']([^"']+)/i) || h.match(/href=["']([^"']+)["'][^>]*rel=["']canonical/i) || [])[1] || '' };
      } catch (e) { titles[u] = { title: '', err: true }; } }));
    window.tdone = true;
  })();
  return { sitemaps: seen.size, urls: urls.length };
};
// Bước 2: khi tdone === true, đổi danh sách tiêu đề Google (bỏ "..." ở cuối) thành URL.
window.mapTitles = list => {
  const dp = new DOMParser();
  const n = s => (dp.parseFromString('<p>' + (s || '') + '</p>', 'text/html').body.textContent || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/gi, 'd').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  return list.map(t => {
    const tl = n(String(t).replace(/\s*(\.\.\.|…)\s*$/, ''));
    let m = Object.entries(titles).filter(([u, v]) => v.title && n(v.title).startsWith(tl));
    const live = m.filter(([u, v]) => !v.redirected); if (live.length) m = live;
    let urls = [...new Set(m.map(([u, v]) => v.canon || v.final || u))];
    return { title: t, url: urls.length === 1 ? urls[0] : '', candidates: urls.slice(0, 5) };
  });
};
collect();
```

## Template HTML của trang theo dõi

Thay `__DOMAIN__` trước khi publish. Dữ liệu đọc từ `db` (`ranking/current`, `requests`). Trang không chứa dữ liệu cứng.

```html
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Theo dõi thứ hạng từ khoá – __DOMAIN__</title>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400..700&family=Parkinsans:wght@400..800&display=swap" rel="stylesheet">
<style>
:root {
  --sg-blue: #004AEF; --sg-green: #07EF9C; --sg-cyan: #0FD6F7; --sg-yellow: #FFCE00;
  --sg-blue-nhat: #E5EDFE; --sg-blue-nhat-2: #CCDBFC; --sg-green-nhat: #DFFDF1; --sg-cyan-nhat: #E2FAFE; --sg-yellow-nhat: #FFF6D6;
  --sg-chu: #434343; --sg-den: #1F1F1F; --sg-xam: #F3F3F3; --sg-vien: #CCDBFC; --sg-trang: #FFFFFF; --sg-tong: #D9DCE8;
  --sg-gradient: linear-gradient(90deg, #004AEF 0%, #07EF9C 100%);
  --sg-font: "Google Sans", Arial, sans-serif;
  --sg-bo-goc: 16px;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: var(--sg-font); color: var(--sg-chu); background: var(--sg-trang); font-size: 14px; }
button, input, select { font-family: var(--sg-font); }
.topbar { background: var(--sg-blue); color: var(--sg-trang); padding: 14px 28px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brand { font-weight: 700; letter-spacing: .5px; font-size: 18px; }
.tagline { font-size: 12px; opacity: .95; }
.tagline b { color: var(--sg-green); font-weight: 600; }
.hero { background: var(--sg-gradient); color: var(--sg-trang); padding: 22px 28px 26px; }
.hero h1 { margin: 0 0 6px; font-size: 24px; color: var(--sg-trang); font-weight: 700; }
.hero .meta { font-size: 13px; display: flex; flex-wrap: wrap; gap: 6px 22px; }
.hero .meta span b { font-weight: 600; }
main { padding: 20px 28px 48px; max-width: 1400px; margin: 0 auto; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat { border: 1px solid var(--sg-vien); border-radius: var(--sg-bo-goc); padding: 14px 16px; background: var(--sg-trang); cursor: pointer; transition: border-color .15s; }
.stat:hover, .stat.on { border-color: var(--sg-blue); background: var(--sg-blue-nhat); }
.stat .n { font-size: 26px; font-weight: 700; color: var(--sg-blue); line-height: 1.1; }
.stat .l { font-size: 12px; margin-top: 4px; color: var(--sg-chu); }
.status { border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.status.ok { background: var(--sg-green-nhat); color: var(--sg-den); }
.status.warn { background: var(--sg-yellow-nhat); color: var(--sg-den); border-left: 4px solid var(--sg-yellow); }
.status.info { background: var(--sg-blue-nhat); color: var(--sg-den); border-left: 4px solid var(--sg-blue); }
.status .txt { line-height: 1.5; }
.toolbar { position: sticky; top: 0; z-index: 5; background: var(--sg-trang); padding: 10px 0; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; border-bottom: 1px solid var(--sg-xam); margin-bottom: 8px; }
.toolbar input[type=search] { flex: 1 1 240px; min-width: 200px; padding: 10px 14px; border: 1px solid var(--sg-vien); border-radius: 999px; font-size: 14px; color: var(--sg-den); outline: none; }
.toolbar input[type=search]:focus { border-color: var(--sg-blue); }
.nut { background: var(--sg-blue); color: var(--sg-trang); border: 0; border-radius: 999px; padding: 10px 18px; font-weight: 600; cursor: pointer; font-size: 14px; white-space: nowrap; }
.nut:disabled { opacity: .5; cursor: default; }
.nut.phu { background: var(--sg-trang); color: var(--sg-blue); border: 1px solid var(--sg-blue); }
.nut.cta { background: var(--sg-yellow); color: var(--sg-den); }
.nut.nho { padding: 6px 12px; font-size: 13px; }
.hidden { display: none !important; }
.selbar { display: flex; align-items: center; gap: 10px; background: var(--sg-yellow-nhat); border-radius: 999px; padding: 4px 4px 4px 14px; }
.selbar .c { font-weight: 600; color: var(--sg-den); font-size: 13px; }
.link { background: none; border: 0; color: var(--sg-blue); cursor: pointer; font-size: 13px; padding: 4px 6px; text-decoration: underline; }
.tbl-wrap { border: 1px solid var(--sg-vien); border-radius: 12px; overflow: auto; }
table { width: 100%; border-collapse: collapse; }
thead th { background: var(--sg-blue); color: var(--sg-trang); font-weight: 600; text-align: left; padding: 11px 12px; font-size: 13px; position: sticky; top: 0; white-space: nowrap; }
thead th.sortable { cursor: pointer; user-select: none; }
tbody td { padding: 9px 12px; border-top: 1px solid var(--sg-xam); vertical-align: middle; }
tbody tr:nth-child(even) td { background: var(--sg-xam); }
tbody tr.sel td { background: var(--sg-blue-nhat) !important; }
td.kw { color: var(--sg-den); font-weight: 500; }
td.pos { white-space: nowrap; }
.badge { display: inline-block; min-width: 34px; text-align: center; padding: 3px 9px; border-radius: 999px; font-weight: 700; font-size: 13px; }
.b1 { background: var(--sg-green); color: var(--sg-den); }
.b3 { background: var(--sg-cyan); color: var(--sg-den); }
.b10 { background: var(--sg-blue-nhat-2); color: var(--sg-blue); }
.b30 { background: var(--sg-xam); color: var(--sg-chu); border: 1px solid var(--sg-tong); }
.bout { background: var(--sg-trang); color: var(--sg-chu); border: 1px dashed var(--sg-chu); font-weight: 500; }
.delta { font-size: 12px; margin-left: 6px; color: var(--sg-chu); }
.delta.up { color: var(--sg-blue); font-weight: 600; }
td.url a { color: var(--sg-blue); text-decoration: none; word-break: break-all; font-size: 13px; }
td.url a:hover { text-decoration: underline; }
td.url .none { color: var(--sg-chu); }
.st { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.st.ok { background: var(--sg-green-nhat); color: var(--sg-den); }
.st.warn { background: var(--sg-yellow-nhat); color: var(--sg-den); border: 1px solid var(--sg-yellow); }
.st.error { background: var(--sg-yellow); color: var(--sg-den); }
.st.pending { background: var(--sg-cyan-nhat); color: var(--sg-den); border: 1px solid var(--sg-cyan); }
.note { display: block; font-size: 12px; color: var(--sg-chu); margin-top: 3px; max-width: 260px; }
input[type=checkbox] { width: 17px; height: 17px; accent-color: var(--sg-blue); cursor: pointer; }
.empty { padding: 40px; text-align: center; color: var(--sg-chu); }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: var(--sg-den); color: var(--sg-trang); padding: 10px 18px; border-radius: 999px; font-size: 13px; z-index: 20; }
.modal-bg { position: fixed; inset: 0; background: rgba(31,31,31,.45); display: flex; align-items: center; justify-content: center; z-index: 30; padding: 16px; }
.modal { background: var(--sg-trang); border-radius: var(--sg-bo-goc); padding: 24px; max-width: 520px; width: 100%; }
.modal h3 { margin: 0 0 10px; color: var(--sg-blue); font-size: 18px; }
.modal p { margin: 0 0 12px; line-height: 1.55; }
.modal .cmd { background: var(--sg-xam); border-radius: 10px; padding: 10px 12px; font-size: 13px; color: var(--sg-den); margin-bottom: 14px; }
.modal .row { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
.history { margin-top: 22px; }
.history h2 { font-size: 16px; margin: 0 0 8px; color: var(--sg-blue); }
.history ul { margin: 0; padding-left: 18px; line-height: 1.7; font-size: 13px; }
footer { background: var(--sg-blue); color: var(--sg-trang); font-size: 12px; padding: 10px 28px; display: flex; justify-content: space-between; }
footer .g { color: var(--sg-green); font-weight: 600; }
@media (max-width: 720px) { .topbar, .hero, main, footer { padding-left: 14px; padding-right: 14px; } .tagline { display: none; } .note { max-width: none; } }
</style>
</head>
<body>
<div class="topbar">
  <div class="brand">SEONGON</div>
  <div class="tagline"><b>AI-First</b> ↗ Search Marketing Growth Partner</div>
</div>
<div class="hero">
  <h1>Theo dõi thứ hạng từ khoá – <span id="hDomain">__DOMAIN__</span></h1>
  <div class="meta">
    <span>Lần check gần nhất: <b id="mCheckedAt">—</b></span>
    <span>Số từ khoá: <b id="mTotal">—</b></span>
    <span id="mMethod">Google.com.vn, tiếng Việt, máy tính, phiên chưa đăng nhập (tương đương ẩn danh)</span>
  </div>
</div>

<main>
  <div class="stats" id="stats"></div>
  <div id="statusBox" class="status info"><div class="txt">Đang tải dữ liệu…</div></div>

  <div class="toolbar">
    <input type="search" id="q" placeholder="Tìm từ khoá hoặc URL…" aria-label="Tìm từ khoá">
    <div class="selbar hidden" id="selbar">
      <span class="c" id="selCount">0 từ khoá đã chọn</span>
      <button class="link" id="btnClear">Bỏ chọn</button>
      <button class="nut cta" id="btnRecheck">Check lại</button>
    </div>
    <button class="nut phu" id="btnCopy">Copy bảng</button>
  </div>

  <div class="tbl-wrap">
    <table>
      <thead>
        <tr>
          <th style="width:42px"><input type="checkbox" id="chkAll" aria-label="Chọn tất cả"></th>
          <th style="width:44px">#</th>
          <th class="sortable" data-sort="kw">Từ khoá</th>
          <th class="sortable" data-sort="pos" style="width:140px">TOP hiện tại ↕</th>
          <th class="sortable" data-sort="prev" style="width:130px" id="thPrev">TOP lần trước ↕</th>
          <th>URL ranking</th>
          <th style="width:250px">Trạng thái</th>
        </tr>
      </thead>
      <tbody id="tbody"><tr><td colspan="7" class="empty">Đang tải dữ liệu…</td></tr></tbody>
    </table>
  </div>

  <div class="history hidden" id="historyBox">
    <h2>Yêu cầu check lại gần đây</h2>
    <ul id="historyList"></ul>
  </div>
</main>
<footer><span>↗ Keyword Ranking Tracker</span><span class="g" id="fDomain">__DOMAIN__</span></footer>

<div id="modal" class="modal-bg hidden" role="dialog" aria-modal="true">
  <div class="modal">
    <h3 id="mdTitle">Đã gửi yêu cầu check lại</h3>
    <p id="mdBody"></p>
    <div class="cmd" id="mdCmd"></div>
    <div class="row">
      <button class="nut phu nho" id="mdCopy">Copy lời nhắn</button>
      <button class="nut nho" id="mdClose">Đóng</button>
    </div>
  </div>
</div>

<script>
(function(){
  const $ = id => document.getElementById(id);
  let rows = [];            // [{kw,pos,url,prev,status,note}]
  let meta = {};
  let requests = [];        // [{id, keywords, status, requestedAt, doneAt}]
  let selected = new Set();
  let filter = 'all';
  let sortBy = null, sortDir = 1;
  let db = null, canWrite = true;

  const posNum = p => (typeof p === 'number' ? p : 999);
  let depth = 20;
  const posText = p => (typeof p === 'number' ? String(p) : 'Ngoài top ' + depth);
  const fmtDate = s => { if (!s) return '—'; const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s)); if (m) return m[3] + '/' + m[2] + '/' + m[1]; const d = new Date(s); if (isNaN(d)) return String(s); return d.toLocaleString('vi-VN', {hour:'2-digit', minute:'2-digit', day:'2-digit', month:'2-digit', year:'numeric'}); };

  function pendingSet(){
    const s = new Set();
    requests.filter(r => r.status === 'pending' || r.status === 'running').forEach(r => (r.keywords||[]).forEach(k => s.add(k)));
    return s;
  }
  function effStatus(r, pend){
    if (pend.has(r.kw)) return 'pending';
    return r.status || 'ok';
  }
  function bucket(p){ if (typeof p !== 'number') return 'out'; if (p === 1) return 't1'; if (p <= 3) return 't3'; if (p <= 10) return 't10'; return 't30'; }

  function renderStats(){
    const c = {t1:0,t3:0,t10:0,t30:0,out:0};
    rows.forEach(r => c[bucket(r.pos)]++);
    const pend = pendingSet();
    const need = rows.filter(r => { const s = effStatus(r, pend); return s === 'warn' || s === 'error'; }).length;
    const items = [['all', rows.length, 'Tất cả từ khoá'],['t1',c.t1,'TOP 1'],['t3',c.t3,'TOP 2–3'],['t10',c.t10,'TOP 4–10'],['t30',c.t30,'TOP 11–' + depth],['out',c.out,'Ngoài top ' + depth],['need',need,'Cần check lại']];
    const box = $('stats'); box.textContent = '';
    items.forEach(([k,n,l]) => {
      const d = document.createElement('div'); d.className = 'stat' + (filter===k?' on':''); d.setAttribute('role','button'); d.tabIndex = 0;
      const a = document.createElement('div'); a.className='n'; a.textContent = n;
      const b = document.createElement('div'); b.className='l'; b.textContent = l;
      d.append(a,b);
      d.onclick = () => { filter = (filter===k && k!=='all') ? 'all' : k; render(); };
      d.onkeydown = e => { if (e.key==='Enter'||e.key===' ') { e.preventDefault(); d.onclick(); } };
      box.appendChild(d);
    });
  }

  function renderStatus(){
    const box = $('statusBox'); box.textContent = '';
    const pend = pendingSet();
    const errs = rows.filter(r => effStatus(r,pend)==='error');
    const warns = rows.filter(r => effStatus(r,pend)==='warn');
    const pendingReq = requests.filter(r => r.status==='pending' || r.status==='running');
    const txt = document.createElement('div'); txt.className='txt';
    let cls = 'ok';
    const parts = [];
    if (pendingReq.length) {
      cls = 'info';
      const n = pend.size;
      const running = pendingReq.some(r=>r.status==='running');
      parts.push((running ? 'Claude đang check lại ' : 'Đang chờ check lại ') + n + ' từ khoá' + (running ? '…' : '. Nhắn Claude "check lại" trong cuộc trò chuyện để bắt đầu.'));
    }
    if (errs.length) { cls = cls==='info'?'info':'warn'; parts.push('⚠ ' + errs.length + ' từ khoá bị lỗi khi check (bị Google chặn hoặc không đọc được kết quả), cần check lại.'); }
    if (warns.length) { cls = cls==='info'?'info':'warn'; parts.push('⚠ ' + warns.length + ' từ khoá biến động mạnh so với lần check trước, nên check lại để xác nhận.'); }
    if (!parts.length) parts.push('✓ Tất cả từ khoá đã được check thành công, không có từ khoá nào cần check lại.');
    box.className = 'status ' + cls;
    parts.forEach((p,i) => { if (i) txt.appendChild(document.createElement('br')); txt.appendChild(document.createTextNode(p)); });
    box.appendChild(txt);
    if (errs.length || warns.length) {
      const b = document.createElement('button'); b.className='nut nho'; b.textContent = 'Chọn các từ khoá cần check lại';
      b.onclick = () => { [...errs, ...warns].forEach(r => selected.add(r.kw)); render(); };
      box.appendChild(b);
    }
  }

  function viewRows(){
    const q = $('q').value.trim().toLowerCase();
    const pend = pendingSet();
    let v = rows.map((r,i) => Object.assign({idx:i+1}, r));
    if (filter === 'need') v = v.filter(r => { const s = effStatus(r,pend); return s==='warn'||s==='error'; });
    else if (filter !== 'all') v = v.filter(r => bucket(r.pos) === filter);
    if (q) v = v.filter(r => r.kw.toLowerCase().includes(q) || (r.url||'').toLowerCase().includes(q));
    if (sortBy === 'prev') v.sort((a,b) => (posNum(a.prev)-posNum(b.prev))*sortDir || a.idx-b.idx);
    if (sortBy === 'pos') v.sort((a,b) => (posNum(a.pos)-posNum(b.pos))*sortDir || a.idx-b.idx);
    if (sortBy === 'kw') v.sort((a,b) => a.kw.localeCompare(b.kw,'vi')*sortDir);
    return v;
  }

  function renderTable(){
    const tb = $('tbody'); tb.textContent = '';
    const pend = pendingSet();
    const v = viewRows();
    if (!v.length) { const tr=document.createElement('tr'); const td=document.createElement('td'); td.colSpan=7; td.className='empty'; td.textContent = rows.length ? 'Không có từ khoá phù hợp.' : 'Chưa có dữ liệu.'; tr.appendChild(td); tb.appendChild(tr); }
    v.forEach(r => {
      const tr = document.createElement('tr'); if (selected.has(r.kw)) tr.className='sel';
      const c0 = document.createElement('td'); const cb = document.createElement('input'); cb.type='checkbox'; cb.checked = selected.has(r.kw); cb.setAttribute('aria-label','Chọn ' + r.kw);
      cb.onchange = () => { cb.checked ? selected.add(r.kw) : selected.delete(r.kw); render(); };
      c0.appendChild(cb);
      const c1 = document.createElement('td'); c1.textContent = r.idx;
      const c2 = document.createElement('td'); c2.className='kw'; c2.textContent = r.kw;
      const cP = document.createElement('td'); cP.className='pos';
      if (r.prev === undefined || r.prev === null || r.prev === '') { const s = document.createElement('span'); s.className='none'; s.textContent='—'; cP.appendChild(s); }
      else { const pb = document.createElement('span'); const pk = bucket(r.prev); pb.className = 'badge ' + ({t1:'b1',t3:'b3',t10:'b10',t30:'b30',out:'bout'})[pk]; pb.textContent = posText(r.prev); cP.appendChild(pb); }
      const c3 = document.createElement('td'); c3.className='pos';
      const bd = document.createElement('span'); const bk = bucket(r.pos);
      bd.className = 'badge ' + ({t1:'b1',t3:'b3',t10:'b10',t30:'b30',out:'bout'})[bk]; bd.textContent = posText(r.pos); c3.appendChild(bd);
      if (r.prev !== undefined && r.prev !== null && r.prev !== '') {
        const pv = r.prev, cur = r.pos; let dt = null, cls = 'delta';
        if (typeof pv === 'number' && typeof cur === 'number') { const d = pv - cur; if (d > 0) { dt = '▲' + d; cls += ' up'; } else if (d < 0) dt = '▼' + (-d); else dt = '='; }
        else if (typeof pv === 'number' && typeof cur !== 'number') dt = '▼';
        else if (typeof pv !== 'number' && typeof cur === 'number') { dt = '▲ mới'; cls += ' up'; }
        if (dt) { const s = document.createElement('span'); s.className = cls; s.textContent = dt; s.title = 'Lần trước: ' + posText(pv); c3.appendChild(s); }
      }
      const c4 = document.createElement('td'); c4.className='url';
      if (r.url && /^https:\/\//.test(r.url)) { const a = document.createElement('a'); a.href = r.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = r.url; c4.appendChild(a); }
      else { const s = document.createElement('span'); s.className='none'; s.textContent = r.url || '—'; c4.appendChild(s); }
      const c5 = document.createElement('td');
      const es = effStatus(r, pend);
      const st = document.createElement('span'); st.className = 'st ' + es;
      st.textContent = ({ok:'OK', warn:'Biến động – nên check lại', error:'Lỗi check – cần check lại', pending:'Đang chờ check lại'})[es] || es;
      c5.appendChild(st);
      if (r.note && es !== 'ok') { const n = document.createElement('span'); n.className='note'; n.textContent = r.note; c5.appendChild(n); }
      tr.append(c0,c1,c2,c3,cP,c4,c5); tb.appendChild(tr);
    });
    const all = $('chkAll'); const vis = v.map(r=>r.kw);
    all.checked = vis.length > 0 && vis.every(k => selected.has(k));
    all.indeterminate = !all.checked && vis.some(k => selected.has(k));
  }

  function renderSel(){
    const n = selected.size;
    $('selbar').classList.toggle('hidden', n === 0);
    $('selCount').textContent = n + ' từ khoá đã chọn';
    $('btnRecheck').textContent = 'Check lại (' + n + ')';
    $('btnRecheck').disabled = !db || !canWrite;
    $('btnCopy').textContent = n ? 'Copy ' + n + ' dòng đã chọn' : 'Copy bảng';
  }

  function renderHistory(){
    const box = $('historyBox'), ul = $('historyList'); ul.textContent = '';
    const list = requests.slice().sort((a,b) => String(b.requestedAt||'').localeCompare(String(a.requestedAt||''))).slice(0,8);
    box.classList.toggle('hidden', !list.length);
    list.forEach(r => {
      const li = document.createElement('li');
      const st = ({pending:'đang chờ', running:'đang check', done:'đã xong', cancelled:'đã huỷ'})[r.status] || r.status;
      li.textContent = fmtDate(r.requestedAt) + ' – ' + (r.keywords||[]).length + ' từ khoá – ' + st + (r.doneAt ? ' (xong lúc ' + fmtDate(r.doneAt) + ')' : '');
      ul.appendChild(li);
    });
  }

  function render(){
    $('mCheckedAt').textContent = meta.checkedAt ? fmtDate(meta.checkedAt) : '—';
    $('mTotal').textContent = rows.length || '—';
    if (meta.method) $('mMethod').textContent = meta.method;
    if (meta.domain) { $('hDomain').textContent = meta.domain; $('fDomain').textContent = meta.domain; }
    $('thPrev').textContent = 'TOP lần trước' + (meta.prevCheckedAt ? ' (' + fmtDate(meta.prevCheckedAt).slice(0,5) + ')' : '') + ' ↕';
    renderStats(); renderStatus(); renderTable(); renderSel(); renderHistory();
  }

  // ---- events
  $('q').addEventListener('input', renderTable);
  $('chkAll').addEventListener('change', e => { const vis = viewRows().map(r=>r.kw); vis.forEach(k => e.target.checked ? selected.add(k) : selected.delete(k)); render(); });
  $('btnClear').onclick = () => { selected.clear(); render(); };
  document.querySelectorAll('th.sortable').forEach(th => th.onclick = () => { const k = th.dataset.sort; if (sortBy === k) { if (sortDir === 1) sortDir = -1; else { sortBy = null; sortDir = 1; } } else { sortBy = k; sortDir = 1; } renderTable(); });

  function toast(msg){ const t = document.createElement('div'); t.className='toast'; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 2200); }
  async function copyText(text){
    try { await navigator.clipboard.writeText(text); return true; } catch(e) {}
    try { const ta = document.createElement('textarea'); ta.value = text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); const ok = document.execCommand('copy'); ta.remove(); return ok; } catch(e) { return false; }
  }
  $('btnCopy').onclick = async () => {
    const src = selected.size ? rows.filter(r => selected.has(r.kw)) : viewRows();
    const lines = ['Từ khoá\tTOP hiện tại\tURL ranking'].concat(src.map(r => [r.kw, posText(r.pos), r.url || '—'].join('\t')));
    const ok = await copyText(lines.join('\n'));
    toast(ok ? 'Đã copy ' + src.length + ' dòng – dán thẳng vào Google Sheet/Excel' : 'Trình duyệt chặn copy, hãy thử lại');
  };

  let lastCmd = '';
  $('btnRecheck').onclick = async () => {
    if (!db || !selected.size) return;
    const kws = rows.map(r=>r.kw).filter(k => selected.has(k));
    const btn = $('btnRecheck'); btn.disabled = true; btn.textContent = 'Đang gửi…';
    try {
      const id = 'r' + Date.now();
      await db.collection('requests').doc(id).set({ keywords: kws, status: 'pending', requestedAt: new Date().toISOString() });
      lastCmd = 'Check lại ranking các từ khoá tôi vừa chọn trên trang theo dõi thứ hạng ' + (meta.domain || '');
      $('mdTitle').textContent = 'Đã gửi yêu cầu check lại ' + kws.length + ' từ khoá';
      $('mdBody').textContent = 'Yêu cầu đã được lưu. Claude không tự chạy khi bạn bấm nút, nên hãy quay lại cuộc trò chuyện với Claude và gửi lời nhắn bên dưới. Claude sẽ check lại ở phiên chưa đăng nhập và cập nhật kết quả thẳng vào trang này.';
      $('mdCmd').textContent = lastCmd;
      $('modal').classList.remove('hidden');
      selected.clear();
    } catch (e) {
      toast(e && e.code === 'invalid_argument' ? 'Bạn chỉ có quyền xem, không gửi được yêu cầu' : 'Không gửi được yêu cầu, hãy thử lại');
      if (e && e.code === 'invalid_argument') canWrite = false;
    }
    render();
  };
  $('mdClose').onclick = () => $('modal').classList.add('hidden');
  $('mdCopy').onclick = async () => { const ok = await copyText(lastCmd); toast(ok ? 'Đã copy lời nhắn' : 'Không copy được'); };

  // ---- data
  render();
  const loadTimer = setTimeout(() => { if (!rows.length) { const b = $('statusBox'); b.className='status warn'; b.textContent = 'Chưa tải được dữ liệu. Kiểm tra kết nối mạng hoặc đăng nhập claude.ai rồi mở lại trang.'; } }, 10000);
  (async () => {
    let api = null;
    try { api = window.claude && window.claude.use ? await window.claude.use('db') : null; } catch(e) { api = null; }
    if (!api) { clearTimeout(loadTimer); const b = $('statusBox'); b.className='status warn'; b.textContent = 'Trang này cần đăng nhập claude.ai để đọc dữ liệu thứ hạng.'; $('tbody').innerHTML = '<tr><td colspan="7" class="empty">Không đọc được dữ liệu.</td></tr>'; return; }
    db = api;
    db.doc('ranking/current').onSnapshot(snap => {
      if (!snap.metadata.fromCache) clearTimeout(loadTimer);
      const d = snap.exists ? snap.data() : null;
      if (d) { rows = Array.isArray(d.rows) ? d.rows.map(r => Object.assign({}, r)) : []; meta = { checkedAt: d.checkedAt, method: d.method, prevCheckedAt: d.prevCheckedAt, domain: d.domain }; if (typeof d.depth === 'number') depth = d.depth; }
      else { rows = []; meta = {}; }
      const kws = new Set(rows.map(r=>r.kw)); [...selected].forEach(k => { if (!kws.has(k)) selected.delete(k); });
      render();
    }, err => { clearTimeout(loadTimer); const b = $('statusBox'); b.className='status warn'; b.textContent = 'Không tải được dữ liệu (' + (err && err.code || 'lỗi') + ').'; });
    db.collection('requests').onSnapshot(snap => {
      requests = snap.docs.map(d => Object.assign({ id: d.id }, d.data()));
      render();
    }, () => {});
  })();
})();
</script>
</body>
</html>
```