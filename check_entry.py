# -*- coding: utf-8 -*-
"""
Check a specific entry to verify columns
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}
ds_id = "a5575563-f29c-4224-b6e8-1b804bf04ba6"

# Get all entries
r = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
items = r.json().get('results', [])

# Find 周日011 entry
for item in items:
    name = item.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
    if '周日011' in name:
        print(f"Found: {name}")
        props = item.get('properties', {})
        for k, v in props.items():
            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
        break
