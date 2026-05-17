# -*- coding: utf-8 -*-
"""
Check database schema and add columns
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

# Get database schema
r = requests.get('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b', headers=h)
d = r.json()

print("Database properties:")
props = d.get('properties', {})
for k, v in props.items():
    print(f"  {k}: {v.get('type')}")

if not props:
    print("  (empty)")

# Try to add columns
print("\nAdding columns...")
r2 = requests.patch('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b',
                   json={
                       "properties": {
                           "让球预测": {
                               "select": {
                                   "options": [
                                       {"name": "主胜"},
                                       {"name": "平局"},
                                       {"name": "客胜"},
                                   ]
                               }
                           },
                           "让球预测正确": {
                               "checkbox": {}
                           },
                       }
                   },
                   headers=h)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:500]}")

# Verify
r3 = requests.get('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b', headers=h)
d3 = r3.json()
props3 = d3.get('properties', {})
print(f"\nAfter adding - properties: {list(props3.keys())}")
