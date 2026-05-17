# -*- coding: utf-8 -*-
"""
Test: Create a single entry with new columns to see if they auto-create
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

NOTION_KEY = "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"
h = {'Authorization': 'Bearer ' + NOTION_KEY, 'Notion-Version': '2025-09-03'}
DB_ID = "7ee379c2f4364d558b6b5b8c48d1b00b"

# Try to create an entry with new columns
payload = {
    "parent": {"database_id": DB_ID},
    "properties": {
        "Name": {"title": [{"text": {"content": "Test 让球预测"}}]},
        "反馈日期": {"date": {"start": "2026-05-05"}},
        "让球预测": {"select": {"name": "主胜"}},
        "让球预测正确": {"checkbox": False},
    }
}

print("Creating test entry...")
r = requests.post('https://api.notion.com/v1/pages', json=payload, headers=h)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

if r.status_code == 200:
    entry_id = r.json().get('id')
    print(f"Entry created: {entry_id}")
    
    # Now check database schema again
    r2 = requests.get(f'https://api.notion.com/v1/databases/{DB_ID}', headers=h)
    d2 = r2.json()
    props = d2.get('properties', {})
    print(f"\nDatabase properties after creation: {list(props.keys())}")
    
    # Delete the test entry
    r3 = requests.patch(f'https://api.notion.com/v1/pages/{entry_id}', 
                       json={"archived": True}, headers=h)
    print(f"Test entry deleted: {r3.status_code}")
