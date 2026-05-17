# -*- coding: utf-8 -*-
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

# Get all entries
ds_id = "a5575563-f29c-4224-b6e8-1b804bf04ba6"
r = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
items = r.json().get('results', [])

print(f"Total entries: {len(items)}")

# Check first entry properties
if items:
    entry = items[0]
    props = entry.get('properties', {})
    print(f"\nFirst entry properties:")
    for k, v in props.items():
        print(f"  {k}: type={v.get('type')}")
    
    # Check a match entry (not summary)
    for item in items:
        name = item.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
        if '第' in name or '场' in name:
            print(f"\nMatch entry: {name}")
            props = item.get('properties', {})
            for k, v in props.items():
                print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:100]}")
            break
