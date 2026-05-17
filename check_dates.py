import json
import requests
from collections import Counter
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# 查询所有比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛', 'rich_text': {'is_not_empty': True}},
    'page_size': 100
}))
pages = r.json()['results']

# 统计日期
dates = []
for p in pages:
    date_val = p['properties']['比赛日期']['date']['start'] if p['properties']['比赛日期']['date'] else ''
    if date_val:
        dates.append(date_val)

print('各日期比赛数量:')
date_counts = Counter(dates)
for d in sorted(date_counts.keys()):
    print(f'  {d}: {date_counts[d]}场')

print(f'\n总比赛数: {len(pages)}')
print(f'不同日期数: {len(date_counts)}')

# 检查5月10日
print(f'\n5月10日比赛: {date_counts.get("2026-05-10", 0)} 场')

# 列出所有5月10日的比赛名
may10 = []
for p in pages:
    date_val = p['properties']['比赛日期']['date']['start'] if p['properties']['比赛日期']['date'] else ''
    if date_val and '2026-05-10' in date_val:
        name = p['properties']['Name']['title'][0]['plain_text']
        may10.append(name)

if may10:
    print(f'\n5月10日比赛列表 (前10):')
    for n in may10[:10]:
        print(f'  {n}')
else:
    print('\n⚠️ 5月10日比赛不在 Notion 数据库中！')
    print('  之前用 reapply_scores4.py 写入的比分数据不在这个数据库里')
