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
    hd = {'Authorization': 'Bearer ' + key, 'Notion-Version': '2025-09-03', 'Content-Type': 'application/json'}
    body = json.dumps(d, ensure_ascii=False).encode('utf-8') if d else None
    req = urllib.request.Request(url, data=body, headers=hd, method=m)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# 库1: 竞彩比赛追踪 (273条)
print('=== 竞彩比赛追踪 (DB1) ===')
d1 = n('GET', '/v1/databases/35491ad7-17ba-81cc-aa04-ce53f7234e17')
for k, v in sorted(d1.get('properties',{}).items(), key=lambda x: x[0].encode('utf-8').hex()):
    print(f'  {k.encode("utf-8").hex()[:30]} | {k:20s} | {v["type"]}')

print()
# 读几条
q1 = n('POST', '/v1/search', {'page_size': 100})
db1 = [p for p in q1['results'] if p.get('parent',{}).get('database_id')=='35491ad7-17ba-81cc-aa04-ce53f7234e17']
print(f'竞彩追踪样本: {len(db1)} 条')
for p in db1[:3]:
    props = p['properties']
    title = props.get('Name',{}).get('title',['?'])[0].get('plain_text','?') if props.get('Name',{}).get('title') else '?'
    print(f'  [{title}]')

# 库2: 竞彩 (19条)
print('\n=== 竞彩 (DB2) ===')
d2 = n('GET', '/v1/databases/35d91ad7-17ba-80fb-a45c-cb6471eaf4d9')
for k, v in sorted(d2.get('properties',{}).items(), key=lambda x: x[0].encode('utf-8').hex()):
    print(f'  {k.encode("utf-8").hex()[:30]} | {k:20s} | {v["type"]}')

print()
q2 = n('POST', '/v1/search', {'page_size': 100})
db2 = [p for p in q2['results'] if p.get('parent',{}).get('database_id')=='35d91ad7-17ba-80fb-a45c-cb6471eaf4d9']
print(f'竞彩样本: {len(db2)} 条')
for p in db2[:5]:
    props = p['properties']
    title = props.get('Name',{}).get('title',['?'])[0].get('plain_text','?') if props.get('Name',{}).get('title') else '?'
    print(f'  [{title}]')
    for k,v in props.items():
        h = k.encode('utf-8').hex()
        if v['type']=='rich_text' and v.get('rich_text') and v['rich_text'][0]['plain_text']:
            print(f'    {h[:20]}={v["rich_text"][0]["plain_text"][:50]}')
        elif v['type']=='number' and v.get('number') is not None:
            print(f'    {h[:20]}={v["number"]}')
        elif v['type']=='select' and v.get('select'):
            print(f'    {h[:20]}={v["select"]["name"]}')
        elif v['type']=='date' and v.get('date'):
            print(f'    {h[:20]}={v["date"]["start"]}')
        elif v['type']=='url' and v.get('url'):
            print(f'    {h[:20]}={v["url"]}')
