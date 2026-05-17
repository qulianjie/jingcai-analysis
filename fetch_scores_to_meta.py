# -*- coding: utf-8 -*-
"""从Notion拉取实际比分，写入meta.json，然后跑组合分析"""
import os, json, re, requests

# Notion配置
API_KEY = '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'
DB_ID = '35491ad7-17ba-818d-b7cc-d8a433d05229'

def notion_request(method, path, body=None):
    data = json.dumps(body).encode('utf-8') if body else b''
    headers = {
        'Authorization': 'Bearer ' + API_KEY,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
        'Content-Length': str(len(data))
    }
    url = 'https://api.notion.com' + path
    r = requests.request(method, url, headers=headers, data=data, timeout=15)
    return r.json()

# 1. 从Notion拉所有记录
print('从Notion拉取比分...')
all_results = []
cursor = None
while True:
    body = {'page_size': 100}
    if cursor:
        body['start_cursor'] = cursor
    data = notion_request('POST', '/v1/databases/' + DB_ID + '/query', body)
    all_results.extend(data.get('results', []))
    if not data.get('has_more'):
        break
    cursor = data['next_cursor']

print(f'找到 {len(all_results)} 条记录')

# 2. 提取比分映射
score_map = {}
for page in all_results:
    props = page.get('properties', {})
    match_num = ''
    for k, v in props.items():
        if v.get('type') == 'rich_text':
            txt = v.get('rich_text', [{}])[0].get('plain_text', '')
            if txt and ('周' in txt):
                match_num = txt
                break
    score = ''
    for k, v in props.items():
        if '比分' in k and v.get('type') == 'rich_text':
            score = v.get('rich_text', [{}])[0].get('plain_text', '')
            break
    if match_num and score:
        score_map[match_num] = score

print(f'有比分的: {len(score_map)}场')
for k, v in sorted(score_map.items()):
    print(f'  {k}: {v}')

# 3. 写入meta.json
BASE = os.path.join('jingcai', 'tasks')
updated = 0
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    date_updated = 0
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not (os.path.isdir(mp) and m.startswith('match')):
            continue
        meta_path = os.path.join(mp, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        matchnum = meta.get('matchnum', '')
        
        if matchnum in score_map:
            meta['score'] = score_map[matchnum]
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            updated += 1
            date_updated += 1
    
    if date_updated > 0:
        print(f'  {d}: 更新{date_updated}场')

print(f'\n总更新: {updated}场')
