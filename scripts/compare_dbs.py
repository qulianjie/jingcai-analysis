#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request, json, os
from collections import Counter

with open(os.path.expanduser('~/.config/notion/api_key'), 'rb') as f:
    raw = f.read()
    if raw.startswith(b'\xff\xfe'): raw = raw[2:]
    elif raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
    key = raw.decode('utf-16-le' if b'\x00' in raw[:4] else 'utf-8').strip()

def n(m, p, d=None):
    url = 'https://api.notion.com' + p
    hd = {'Authorization': 'Bearer '+key, 'Notion-Version': '2025-09-03', 'Content-Type': 'application/json'}
    body = json.dumps(d, ensure_ascii=False).encode('utf-8') if d else None
    req = urllib.request.Request(url, data=body, headers=hd, method=m)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

DB_TRACKING = '35491ad7-17ba-81cc-aa04-ce53f7234e17'  # 竞彩比赛追踪
DB_REPORT = '35d91ad7-17ba-80fb-a45c-cb6471eaf4d9'   # 历史每日报告汇总

# 看两个库的字段
print('=== 竞彩比赛追踪 (273条) ===')
r1 = n('GET', f'/v1/databases/{DB_TRACKING}')
props1 = {k:v for k,v in r1.get('properties',{}).items()}
for k,v in sorted(props1.items(), key=lambda x: x[0].encode('utf-8').hex()):
    print(f'  {k.encode("utf-8").hex()[:30]} | {k:20s} | {v["type"]}')

print('\n=== 历史每日报告汇总 (19条) ===')
r2 = n('GET', f'/v1/databases/{DB_REPORT}')
props2 = {k:v for k,v in r2.get('properties',{}).items()}
for k,v in sorted(props2.items(), key=lambda x: x[0].encode('utf-8').hex()):
    print(f'  {k.encode("utf-8").hex()[:30]} | {k:20s} | {v["type"]}')

# 看两个库各自的5条数据
print('\n\n=== 竞彩追踪最后5条（看最近数据）===')
q1 = n('POST', f'/v1/databases/{DB_TRACKING}/query', {'page_size': 5, 'sorts': [{'property': 'e69c88', 'direction': 'descending'}]})
for p in q1['results']:
    t = p['properties'].get('Name',{}).get('title',['?'])[0].get('plain_text','?') if p['properties'].get('Name',{}).get('title') else '?'
    print(f'[{t}]')

print('\n=== 历史报告前5条 ===')
q2 = n('POST', f'/v1/databases/{DB_REPORT}/query', {'page_size': 5})
for p in q2['results']:
    props = p['properties']
    t = props.get('Name',{}).get('title',['?'])[0].get('plain_text','?') if props.get('Name',{}).get('title') else '?'
    print(f'[{t}]')
    for k,v in props.items():
        if v['type']=='rich_text' and v.get('rich_text') and v['rich_text'][0]['plain_text']:
            print(f'  {k.encode("utf-8").hex()[:20]}={v["rich_text"][0]["plain_text"][:40]}')
        elif v['type']=='number' and v.get('number') is not None:
            print(f'  {k.encode("utf-8").hex()[:20]}={v["number"]}')
        elif v['type']=='title' and v.get('title'):
            pass
