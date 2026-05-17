# -*- coding: utf-8 -*-
"""检查05-09在feedback.json中的数据"""
import os, sys, json

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

with open(os.path.join(LEARNINGS_DIR, 'feedback.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', data)
print(f'所有日期: {sorted(dates.keys())}')

if '2026-05-09' in dates:
    d = dates['2026-05-09']
    print(f'05-09 data type: {type(d)}')
    if isinstance(d, dict):
        fb = d.get('feedback', [])
        print(f'05-09 feedback count: {len(fb)}')
        if fb:
            print(f'Sample: {json.dumps(fb[0], ensure_ascii=False)[:300]}')
else:
    print('2026-05-09 not found in feedback.json')
    print(f'Available keys that start with 2026-05: {[k for k in dates.keys() if str(k).startswith("2026-05")]}')
