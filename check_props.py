# -*- coding: utf-8 -*-
"""
Check actual database column types
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}
DB_ID = "7ee379c2f4364d558b6b5b8c48d1b00b"

# Query an existing entry to see what properties exist
ds_id = "a5575563-f29c-4224-b6e8-1b804bf04ba6"
r = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
items = r.json().get('results', [])

print(f"Total entries: {len(items)}")

if items:
    entry = items[0]
    props = entry.get('properties', {})
    print(f"\nProperties from first entry:")
    for k, v in props.items():
        print(f"  {k}: type={v.get('type')}")
