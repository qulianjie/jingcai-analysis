# -*- coding: utf-8 -*-
"""
Exploration script for Notion database structure
"""
import requests, json

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

# Get database structure
r = requests.get('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b', headers=h)
d = r.json()

print("=== Database Info ===")
print("Title:", d.get('title', []))
print("Description:", d.get('description', []))
print("Properties:", json.dumps(d.get('properties', {}), ensure_ascii=False, indent=2))

# Also search all databases
print("\n=== All Databases ===")
r2 = requests.post('https://api.notion.com/v1/search', headers=h, json={'filter': {'property': 'object', 'value': 'database'}})
data = r2.json()
for x in data.get('results', []):
    print(f"ID: {x['id']}, Title: {x.get('title',[])}")
