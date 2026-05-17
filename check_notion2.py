# -*- coding: utf-8 -*-
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {
    'Authorization': 'Bearer ' + NOTION_KEY,
    'Notion-Version': '2025-09-03'
}

db1 = "7ee379c2f4364d558b6b5b8c48d1b00b"
r = requests.get(f'https://api.notion.com/v1/databases/{db1}', headers=h)
d = r.json()
print("=== Database 1 ===")
print("Title:", json.dumps(d.get('title', []), ensure_ascii=False))
print("Properties:", json.dumps(d.get('properties', {}), ensure_ascii=False, indent=2))

# Query items
ds_id = d['data_sources'][0]['id']
r2 = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
items = r2.json().get('results', [])
print(f"\nTotal items: {len(items)}")
for item in items:
    pid = item.get('id')
    props = item.get('properties', {})
    print(f"\nItem {pid}:")
    for k, v in props.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
    # Get page content
    r3 = requests.get(f'https://api.notion.com/v1/blocks/{pid}/children', headers=h)
    blocks = r3.json().get('results', [])
    print(f"  Content blocks: {len(blocks)}")
    for b in blocks[:5]:
        btype = b.get('type', '')
        if btype == 'paragraph':
            text = ''.join([rt.get('plain_text', '') for rt in b['paragraph'].get('rich_text', [])])
            print(f"    [{btype}] {text[:100]}")
        else:
            print(f"    [{btype}]")
