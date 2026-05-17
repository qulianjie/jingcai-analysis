import json
import requests
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
}

r = requests.get(f'https://api.notion.com/v1/databases/{DB_ID}', headers=HEADERS)
print(f'Status: {r.status_code}')
data = r.json()
props = data.get('properties', {})
for k, v in props.items():
    print(f'  {k}: {v.get("type")}')
