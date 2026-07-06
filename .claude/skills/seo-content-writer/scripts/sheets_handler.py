#!/usr/bin/env python3
"""
sheets_handler.py — Đọc input từ Google Sheets, tạo Google Docs, cập nhật URL.

Sheet: https://docs.google.com/spreadsheets/d/1_kQ_BPMuUGPd9aeks7RooMR8dBUbUMQSPaw_2FoMVac
Columns: A=No | B=Anchor text 1 | C=Anchor text 2 | D=Chủ đề | E=Từ khoá chính | F=Google Docs URL

Usage:
  python sheets_handler.py read               # Lấy hàng đầu tiên chưa có Google Docs URL
  python sheets_handler.py read <row>         # Lấy hàng cụ thể
  python sheets_handler.py create-doc <title> # Đọc nội dung từ stdin, tạo Google Doc
  python sheets_handler.py update <row> <url> # Điền Google Docs URL vào sheet
"""

import json
import sys
import os

SKILL_DIR = os.path.expanduser('~/.claude/skills/seo-content-writer')
SPREADSHEET_ID = '1_kQ_BPMuUGPd9aeks7RooMR8dBUbUMQSPaw_2FoMVac'
SHEET_RANGE = 'A:F'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
]

COL_NO       = 0  # A
COL_ANCHOR1  = 1  # B
COL_ANCHOR2  = 2  # C
COL_TOPIC    = 3  # D
COL_KEYWORD  = 4  # E
COL_DOCS_URL = 5  # F


def get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    token_path  = os.path.join(SKILL_DIR, 'credentials', 'token.json')
    client_path = os.path.join(SKILL_DIR, 'oauth_client.json')

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_path):
                print(
                    'ERROR: oauth_client.json không tìm thấy.\n'
                    f'Đặt file vào: {client_path}\n'
                    'Làm theo BƯỚC 0 trong SKILL.md.',
                    file=sys.stderr
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(client_path, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    return creds


def sheets_service():
    from googleapiclient.discovery import build
    return build('sheets', 'v4', credentials=get_credentials())


def docs_service():
    from googleapiclient.discovery import build
    return build('docs', 'v1', credentials=get_credentials())


def drive_service():
    from googleapiclient.discovery import build
    return build('drive', 'v3', credentials=get_credentials())


def cmd_read(row_num=None):
    svc = sheets_service()
    result = svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_RANGE
    ).execute()

    values = result.get('values', [])
    if not values or len(values) < 2:
        print(json.dumps([], ensure_ascii=False))
        return

    for i, row in enumerate(values[1:], start=2):
        keyword  = row[COL_KEYWORD]  if len(row) > COL_KEYWORD  else ''
        docs_url = row[COL_DOCS_URL] if len(row) > COL_DOCS_URL else ''

        if not keyword:
            continue

        if row_num and str(i) != str(row_num):
            continue

        row_data = {
            'row':     i,
            'no':      row[COL_NO]      if len(row) > COL_NO      else '',
            'anchor1': row[COL_ANCHOR1] if len(row) > COL_ANCHOR1 else '',
            'anchor2': row[COL_ANCHOR2] if len(row) > COL_ANCHOR2 else '',
            'topic':   row[COL_TOPIC]   if len(row) > COL_TOPIC   else '',
            'keyword': keyword,
            'docs_url': docs_url,
        }

        if row_num:
            print(json.dumps(row_data, ensure_ascii=False))
            return

        if not docs_url:
            print(json.dumps(row_data, ensure_ascii=False))
            return

    if row_num:
        print(json.dumps({}, ensure_ascii=False))
    else:
        print(json.dumps({'error': 'no_pending_rows'}, ensure_ascii=False))


def cmd_create_doc(title):
    content = sys.stdin.read()
    if not content.strip():
        print('ERROR: Không có nội dung từ stdin.', file=sys.stderr)
        sys.exit(1)

    d_svc = docs_service()
    dr_svc = drive_service()

    doc    = d_svc.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    d_svc.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'insertText': {'location': {'index': 1}, 'text': content}}]}
    ).execute()

    dr_svc.permissions().create(
        fileId=doc_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    url = f'https://docs.google.com/document/d/{doc_id}/edit'
    print(url)


def cmd_update(row, url):
    col_letter = chr(ord('A') + COL_DOCS_URL)  # → 'F'
    range_name = f'{col_letter}{row}'

    sheets_service().spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body={'values': [[url]]}
    ).execute()

    print(f'OK: Updated row {row} → {url}')


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'read'

    if action == 'read':
        row_num = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_read(row_num)

    elif action == 'create-doc':
        title = sys.argv[2] if len(sys.argv) > 2 else 'Bài SEO'
        cmd_create_doc(title)

    elif action == 'update':
        if len(sys.argv) < 4:
            print('Usage: sheets_handler.py update <row> <url>', file=sys.stderr)
            sys.exit(1)
        cmd_update(int(sys.argv[2]), sys.argv[3])

    else:
        print(f'ERROR: Unknown action "{action}"', file=sys.stderr)
        sys.exit(1)
