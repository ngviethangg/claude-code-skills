#!/usr/bin/env python3
"""
reader.py — Google Docs reader for SEO content review

Usage:
  python reader.py read <google_doc_url>
"""

import json
import sys
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

SKILL_DIR = Path.home() / '.claude/skills/duyet-bai-seo'
CRED_DIR  = SKILL_DIR / 'credentials'
TOKEN_PATH = CRED_DIR / 'token.json'

HEADING_MAP = {
    'HEADING_1': 1, 'HEADING_2': 2, 'HEADING_3': 3,
    'HEADING_4': 4, 'HEADING_5': 5, 'HEADING_6': 6,
}
CONCLUSION_KW = {
    'kết luận', 'tổng kết', 'lời kết', 'tóm lại', 'kết lại', 'kết bài',
    'conclusion', 'summary',
}


def find_oauth_client() -> Path:
    local = SKILL_DIR / 'oauth_client.json'
    if local.exists():
        return local
    fallback = Path.home() / '.claude/skills/seo-content-writer/oauth_client.json'
    if fallback.exists():
        print('  Dùng oauth_client.json từ seo-content-writer', file=sys.stderr)
        return fallback
    print('ERROR: Không tìm thấy oauth_client.json', file=sys.stderr)
    print('  → Đặt tại: ~/.claude/skills/duyet-bai-seo/oauth_client.json', file=sys.stderr)
    print('  → Hoặc copy từ: ~/.claude/skills/seo-content-writer/oauth_client.json', file=sys.stderr)
    sys.exit(1)


def get_credentials() -> Credentials:
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_path = find_oauth_client()
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def extract_doc_id(url: str) -> str:
    m = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return m.group(1)
    raise ValueError(f'Không tìm được Document ID từ URL: {url}')


def parse_doc(doc: dict) -> dict:
    doc_title     = doc.get('title', '')
    body_content  = doc.get('body', {}).get('content', [])
    inline_objects = doc.get('inlineObjects', {})

    paragraphs = []

    for element in body_content:
        if 'paragraph' not in element:
            continue

        para  = element['paragraph']
        style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')

        text_parts = []
        image_ids  = []

        for pe in para.get('elements', []):
            if 'textRun' in pe:
                text_parts.append(pe['textRun'].get('content', ''))
            elif 'inlineObjectElement' in pe:
                image_ids.append(pe['inlineObjectElement'].get('inlineObjectId', ''))

        text = ''.join(text_parts).strip()
        paragraphs.append({'text': text, 'style': style, 'image_ids': image_ids})

    # --- Headings ---
    headings = [
        {'level': HEADING_MAP[p['style']], 'text': p['text']}
        for p in paragraphs
        if p['style'] in HEADING_MAP and p['text']
    ]

    # --- Full text ---
    full_text = '\n'.join(p['text'] for p in paragraphs if p['text'])

    # --- Sapo: first substantial NORMAL_TEXT paragraph ---
    sapo = ''
    for p in paragraphs:
        if p['style'] == 'NORMAL_TEXT' and len(p['text']) > 20:
            sapo = p['text']
            break

    # --- Conclusion: heading with kết keywords + following paras; else last 3 normal ---
    conclusion = ''
    for i, p in enumerate(paragraphs):
        if p['style'] in HEADING_MAP:
            if any(kw in p['text'].lower() for kw in CONCLUSION_KW):
                parts = []
                for q in paragraphs[i + 1:]:
                    if q['style'] in HEADING_MAP:
                        break
                    if q['text']:
                        parts.append(q['text'])
                conclusion = ' '.join(parts)
                break

    if not conclusion:
        normal_texts = [p['text'] for p in paragraphs
                        if p['style'] == 'NORMAL_TEXT' and p['text']]
        conclusion = ' '.join(normal_texts[-3:]) if normal_texts else ''

    # --- Images ---
    images = []
    for i, p in enumerate(paragraphs):
        if not p['image_ids']:
            continue

        # Caption = next short non-heading paragraph
        caption     = ''
        has_caption = False
        if i + 1 < len(paragraphs):
            nxt = paragraphs[i + 1]
            if (nxt['style'] == 'NORMAL_TEXT'
                    and not nxt['image_ids']
                    and nxt['text']
                    and len(nxt['text']) <= 200):
                caption     = nxt['text']
                has_caption = True

        # Alt text from inline object properties
        alt_texts = []
        for obj_id in p['image_ids']:
            if obj_id in inline_objects:
                emb = (inline_objects[obj_id]
                       .get('inlineObjectProperties', {})
                       .get('embeddedObject', {}))
                t = emb.get('title', '').strip()
                d = emb.get('description', '').strip()
                if t or d:
                    alt_texts.append(t or d)

        images.append({
            'has_caption':  has_caption,
            'caption':      caption,
            'has_alt_text': bool(alt_texts),
            'alt_texts':    alt_texts,
        })

    return {
        'doc_title':    doc_title,
        'headings':     headings,
        'sapo':         sapo,
        'conclusion':   conclusion,
        'full_text':    full_text,
        'word_count':   len(full_text.split()),
        'image_count':  len(images),
        'images':       images,
    }


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'read':
        print('Usage: python reader.py read <google_doc_url>', file=sys.stderr)
        sys.exit(1)

    url = sys.argv[2]
    try:
        doc_id = extract_doc_id(url)
    except ValueError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'Đọc tài liệu: {url}', file=sys.stderr)
    creds   = get_credentials()
    service = build('docs', 'v1', credentials=creds)
    doc     = service.documents().get(documentId=doc_id).execute()
    result  = parse_doc(doc)

    print(
        f'  ✓ {result["word_count"]} từ | '
        f'{len(result["headings"])} heading | '
        f'{result["image_count"]} ảnh',
        file=sys.stderr,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
