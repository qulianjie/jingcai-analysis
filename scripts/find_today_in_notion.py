#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request, json, os

with open(os.path.expanduser('~/.config/notion/api_key'), 'rb') as f:
    raw = f.read()
    if raw.startswith(b'\xff\xfe'): raw = raw[2:]
    elif raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
    key = raw.decode('utf-16-le' if b'\x00' in raw[:4] else 'utf-8').strip()

def notion(m, p, d=None):
    url = 'https://api.notion.com' + p
    hd = {'Authorization': 'Bearer '+key, 'Notion-Version': '2025-09-03', 'Content-Type': 'application/json'}
    body = json.dumps(d, ensure_ascii=False).encode('utf-8') if d else None
    req = urllib.request.Request(url, data=body, headers=hd, method=m)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# 搜索今天（2026-05-18）相关记录
r = notion('POST', '/v1/search', {'page_size': 100})
pages = [p for p in r['results'] if p.get('parent',{}).get('database_id')=='35491ad7-17ba-81cc-aa04-ce53f7234e17']

# 继续获取后续页
for _ in range(3):
    if not r.get('has_more') or not r.get('next_cursor'): break
    r = notion('POST', '/v1/search', {'page_size': 100, 'start_cursor': r['next_cursor']})
    pages.extend([p for p in r['results'] if p.get('parent',{}).get('database_id')=='35491ad7-17ba-81cc-aa04-ce53f7234e17'])

print(f'总记录: {len(pages)}')

# 搜索拉赫蒂、佐加顿斯、厄格里特、阿森纳
today_matches = ['拉赫蒂', '佐加顿斯', '厄格里特', '阿森纳']
HEX_JC = 'e7ab9ee5bda9e6aca7e8b594e8839c'
HEX_RQ = 'e8aea9e79083e9a284e6b58b'
HEX_ZJ = 'e6ada532365fe5ba84e5aeb6e69c80e79c8be5a5bd'

for target in today_matches:
    found = False
    for p in pages:
        props = p['properties']
        if not props.get('Name',{}).get('title') or len(props['Name']['title']) == 0:
            continue
        title = props['Name']['title'][0]['plain_text']
        if target in title:
            found = True
            jc = ''
            if HEX_JC in props and props[HEX_JC].get('number') is not None:
                jc = props[HEX_JC]['number']
            rq = ''
            if HEX_RQ in props and props[HEX_RQ].get('rich_text') and len(props[HEX_RQ]['rich_text']) > 0:
                rq = props[HEX_RQ]['rich_text'][0]['plain_text'][:50]
            zj = ''
            if HEX_ZJ in props and props[HEX_ZJ].get('rich_text') and len(props[HEX_ZJ]['rich_text']) > 0:
                zj = props[HEX_ZJ]['rich_text'][0]['plain_text']
            print(f'✅ {title}')
            print(f'   竞彩胜值: {jc}')
            print(f'   庄家看好: {zj}')
            print(f'   让球预测: {rq}')
            break
    if not found:
        print(f'❌ {target}: 未找到')
