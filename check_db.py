# -*- coding: utf-8 -*-
"""
Check database schema - what properties exist?
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

# Get database schema
r = requests.get('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b', headers=h)
d = r.json()

print("Full database response:")
print(json.dumps(d, ensure_ascii=False, indent=2)[:3000])
