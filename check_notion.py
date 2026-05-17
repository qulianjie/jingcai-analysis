# -*- coding: utf-8 -*-
import requests, json

NOTION_KEY = "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"
h = {
    'Authorization': 'Bearer ' + NOTION_KEY,
    'Notion-Version': '2025-09-03'
}

# Check both databases
db1 = "7ee379c2f4364d558b6b5b8c48d1b00b"
db2 = "35491ad717ba81ccaa04ce53f7234e17"

for db_id, label in [(db1, "Database 1"), (db2, "Database 2")]:
    print(f"\n=== {label}: {db_id} ===")
    r = requests.get(f'https://api.notion.com/v1/databases/{db_id}', headers=h)
    d = r.json()
    print(f"  Title: {d.get('title',[])}")
    print(f"  Properties: {list(d.get('properties',{}).keys())}")
    
    # Try query with data_sources endpoint
    ds_list = d.get('data_sources', [])
    if ds_list:
        ds_id = ds_list[0].get('id')
        print(f"  Data source ID: {ds_id}")
        r2 = requests.post(f'https://api.notion.com/v1/data_sources/{ds_id}/query', headers=h, json={})
        if r2.status_code == 200:
            items = r2.json().get('results', [])
            print(f"  Total items: {len(items)}")
            for item in items[:3]:
                props = item.get('properties', {})
                title_prop = props.get('Name') or props.get('Title') or props.get('名称') or props.get('title') or list(props.values())[0] if props else None
                if title_prop:
                    print(f"    - {title_prop}")
                else:
                    print(f"    - {list(props.keys())}")
        else:
            print(f"  Query failed: {r2.status_code} - {r2.text[:200]}")
