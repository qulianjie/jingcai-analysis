# -*- coding: utf-8 -*-
import requests, json

NOTION_KEY = "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"
h = {
    'Authorization': 'Bearer ' + NOTION_KEY,
    'Notion-Version': '2025-09-03'
}

# Search for pages in the database
r = requests.post('https://api.notion.com/v1/search', headers=h, json={
    'filter': {
        'value': 'database',
        'property': 'object'
    }
})
print("=== All databases ===")
for item in r.json().get('results', []):
    db_id = item.get('id')
    title = item.get('title', [])
    if title:
        plain = title[0].get('text', {}).get('content', '') if title else ''
    else:
        plain = ''
    print(f"  {db_id} - {plain}")

# Get parent page children (database should be listed)
print("\n=== Parent page children ===")
r2 = requests.get('https://api.notion.com/v1/blocks/35391ad7-17ba-804d-8e5b-ec1b55fe2f71/children', headers=h)
for block in r2.json().get('results', []):
    print(f"  {block.get('type')} - {block.get('id')}")
