# -*- coding: utf-8 -*-
"""检查step25数据结构"""
import os, sys, json

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# Find step25 files
for date in ['2026-05-03', '2026-05-04', '2026-05-05']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    if not os.path.exists(data_dir):
        continue
    for md in sorted(os.listdir(data_dir))[:3]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        s25_path = os.path.join(md_path, 'step25_zhuangjia.json')
        if os.path.exists(s25_path):
            s25 = json.loads(rd(s25_path))
            print(f'=== {md} ===')
            print(f'  data: {json.dumps(s25.get("data", {}), ensure_ascii=False)[:200]}')
            print(f'  labels: {json.dumps(s25.get("labels", {}), ensure_ascii=False)[:200]}')
            print(f'  conclusion: {json.dumps(s25.get("conclusion", {}), ensure_ascii=False)}')
            print()
            break
