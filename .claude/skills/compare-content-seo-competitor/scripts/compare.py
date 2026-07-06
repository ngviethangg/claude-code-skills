#!/usr/bin/env python3
"""
compare.py — SEO Content Competitor Analyzer

Crawl URLs, extract structured content, output JSON for Claude to analyze.

Usage:
  python compare.py crawl <url>                       # Crawl single URL
  python compare.py crawl <url1> <url2> <url3> ...    # Crawl multiple URLs
"""

import json
import sys
import re
import os
from collections import Counter
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

VI_STOPWORDS = {
    # Vietnamese
    'và', 'của', 'là', 'trong', 'có', 'được', 'cho', 'với', 'các', 'này',
    'một', 'từ', 'đến', 'bạn', 'khi', 'nếu', 'để', 'tại', 'những', 'về',
    'theo', 'như', 'đây', 'cũng', 'tôi', 'bởi', 'vì', 'hay', 'hoặc', 'mà',
    'thì', 'sẽ', 'đã', 'đang', 'sự', 'cần', 'nhiều', 'hơn', 'nhất', 'rất',
    'nên', 'nào', 'chỉ', 'còn', 'qua', 'trên', 'dưới', 'sau', 'trước',
    'giữa', 'tất', 'mọi', 'đó', 'ai', 'gì', 'đều', 'lại', 'ngay', 'luôn',
    'thế', 'nữa', 'ra', 'vào', 'lên', 'xuống', 'thêm', 'bao', 'giờ',
    'cả', 'nhau', 'ta', 'anh', 'chị', 'em', 'họ', 'mình', 'người', 'việc',
    'không', 'phải', 'nếu', 'vậy', 'thật', 'mới', 'chưa', 'nhưng', 'đã',
    'dù', 'dù', 'tuy', 'vẫn', 'hãy', 'mỗi', 'tức', 'như', 'chính',
    # English
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'that', 'this', 'these', 'those',
    'it', 'its', 'not', 'no', 'up', 'out', 'so', 'if', 'about', 'into',
    'than', 'then', 'when', 'where', 'which', 'who', 'what', 'how', 'all',
    'can', 'also', 'just', 'more', 'some', 'any', 'each', 'most', 'other',
}

CONCLUSION_KW = {
    'kết luận', 'tổng kết', 'lời kết', 'tóm lại', 'tổng quan', 'kết lại',
    'conclusion', 'summary', 'final thoughts', 'in conclusion', 'wrap up',
}

FORMAT_LABELS = {
    'has_table':       'Bảng (table)',
    'has_ol':          'Danh sách đánh số (ordered list)',
    'has_ul':          'Danh sách bullet (unordered list)',
    'has_blockquote':  'Trích dẫn nổi bật (blockquote)',
    'has_faq':         'Mục FAQ / Hỏi đáp',
    'has_conclusion':  'Mục Kết luận / Tổng kết',
    'has_table_of_contents': 'Mục lục bài viết (TOC)',
}


def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def extract_words(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\d+', '', text)
    words = re.findall(
        r"[a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ']+",
        text
    )
    return [w for w in words if len(w) >= 3 and w not in VI_STOPWORDS]


def extract_bigrams(words: list[str]) -> list[str]:
    return [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]


def crawl_url(url: str) -> dict:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        # Prefer charset from meta tag; fallback to apparent_encoding
        detected = resp.apparent_encoding or 'utf-8'
        resp.encoding = detected
    except Exception as e:
        return {'url': url, 'error': str(e), 'domain': urlparse(url).netloc}

    soup = BeautifulSoup(resp.text, 'lxml')

    # Strip noise
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                               'aside', 'noscript', 'iframe', 'form']):
        tag.decompose()

    # --- Basic metadata ---
    title = clean_text(soup.title.get_text()) if soup.title else ''
    h1_tag = soup.find('h1')
    h1 = clean_text(h1_tag.get_text()) if h1_tag else ''

    # --- Headings ---
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f'h{level}'):
            text = clean_text(tag.get_text())
            if text and len(text) > 2:
                headings.append({'level': level, 'text': text})

    # --- Format elements ---
    has_table      = bool(soup.find('table'))
    has_ol         = bool(soup.find('ol'))
    has_ul         = bool(soup.find('ul'))
    has_blockquote = bool(soup.find('blockquote'))

    all_h_text = ' '.join(h['text'].lower() for h in headings)
    has_conclusion = any(kw in all_h_text for kw in CONCLUSION_KW)

    faq_kw = {'faq', 'hỏi đáp', 'câu hỏi thường gặp', 'frequently asked'}
    has_faq = any(kw in all_h_text for kw in faq_kw)

    toc_kw = {'mục lục', 'table of contents', 'nội dung bài'}
    has_toc = any(kw in all_h_text for kw in toc_kw)

    img_count = len(soup.find_all('img', src=True))

    # --- Full text ---
    main = (soup.find('main') or soup.find('article')
            or soup.find(class_=re.compile(r'(content|post|entry|article)', re.I))
            or soup.find('body'))
    text = clean_text(main.get_text(separator=' ')) if main else ''
    word_count = len(text.split())

    # --- Frequency analysis ---
    words    = extract_words(text)
    bigrams  = extract_bigrams(words)
    top_words   = Counter(words).most_common(80)
    top_bigrams = Counter(bigrams).most_common(40)

    return {
        'url':           url,
        'domain':        urlparse(url).netloc,
        'title':         title,
        'h1':            h1,
        'headings':      headings,
        'word_count':    word_count,
        'img_count':     img_count,
        'has_table':          has_table,
        'has_ol':             has_ol,
        'has_ul':             has_ul,
        'has_blockquote':     has_blockquote,
        'has_faq':            has_faq,
        'has_conclusion':     has_conclusion,
        'has_table_of_contents': has_toc,
        'top_words':     top_words,
        'top_bigrams':   top_bigrams,
    }


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'crawl':
        print('Usage: python compare.py crawl <url> [url2] [url3]...', file=sys.stderr)
        sys.exit(1)

    urls = sys.argv[2:]
    results = []
    for url in urls:
        print(f'Đang crawl: {url}', file=sys.stderr)
        data = crawl_url(url)
        results.append(data)
        if 'error' in data:
            print(f'  ⚠ Lỗi: {data["error"]}', file=sys.stderr)
        else:
            print(f'  ✓ {data["word_count"]} từ, {len(data["headings"])} heading', file=sys.stderr)

    print(json.dumps(results, ensure_ascii=False, indent=2))
