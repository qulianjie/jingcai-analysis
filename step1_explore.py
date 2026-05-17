# -*- coding: utf-8 -*-
"""
Step 1: Explore the Notion database
Step 2: Upload jingcai daily reports to Notion
"""
import requests, json

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}

# Get database structure
r = requests.get('https://api.notion.com/v1/databases/7ee379c2f4364d558b6b5b8c48d1b00b', headers=h)
d = r.json()
print("Full DB response:")
print(json.dumps(d, ensure_ascii=False, indent=2))
