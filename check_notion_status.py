# -*- coding: utf-8 -*-
"""
Check current Notion database status
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

import requests, json

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

db_id = "7ee379c2f4364d558b6b5b8c48d1b00b"
ds_id = "a5575563-f29c-4224-b6e8-1b804bf04ba6"

# Get all entries
r = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
items = r.json().get('results', [])

# Group by date
by_date = {}
for item in items:
    props = item.get('properties', {})
    name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', '')
    date_val = props.get('反馈日期', {}).get('date', {})
    date_str = date_val.get('start', 'unknown') if date_val else 'unknown'
    
    if date_str not in by_date:
        by_date[date_str] = []
    by_date[date_str].append(name)

print("=== Notion Database Status ===\n")
for date_str in sorted(by_date.keys()):
    entries = by_date[date_str]
    print(f"[{date_str}] {len(entries)} entries:")
    for e in entries[:5]:
        print(f"  - {e}")
    if len(entries) > 5:
        print(f"  ... and {len(entries)-5} more")
    print()

print(f"Total entries: {len(items)}")
