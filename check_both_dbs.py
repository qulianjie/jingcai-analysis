import json
import requests
from collections import Counter
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'

# 两个数据库都查一下
DB_IDS = {
    '35491ad7-17ba-81cc-aa04-ce53f7234e17': 'DB-3549 (当前)',
    '93490bfb-ac43-49be-a24d-9e3e5a225991': 'DB-9349 (老库)',
}

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

for db_id, db_name in DB_IDS.items():
    print(f'\n{"="*60}')
    print(f'{db_name}: {db_id}')
    print(f'{"="*60}')
    
    # 查询数据库schema
    r = requests.get(f'https://api.notion.com/v1/databases/{db_id}', headers=HEADERS)
    if r.status_code != 200:
        print(f'  无法访问: {r.status_code}')
        continue
    
    props = r.json().get('properties', {})
    print(f'  字段: {list(props.keys())}')
    
    # 查询所有比赛
    r = requests.post(f'https://api.notion.com/v1/databases/{db_id}/query', headers=HEADERS, data=json.dumps({
        'filter': {'property': '比赛', 'rich_text': {'is_not_empty': True}},
        'page_size': 100
    }))
    if r.status_code != 200:
        print(f'  查询失败: {r.status_code} {r.text[:200]}')
        continue
    
    pages = r.json()['results']
    print(f'  比赛总数: {len(pages)}')
    
    # 统计日期
    dates = []
    for p in pages:
        date_val = p['properties']['比赛日期']['date']['start'] if p['properties']['比赛日期']['date'] else ''
        if date_val:
            dates.append(date_val)
    
    date_counts = Counter(dates)
    print(f'  各日期比赛数:')
    for d in sorted(date_counts.keys()):
        print(f'    {d}: {date_counts[d]}场')
    
    # 5月10日
    may10_count = date_counts.get('2026-05-10', 0)
    print(f'  5月10日: {may10_count}场')
