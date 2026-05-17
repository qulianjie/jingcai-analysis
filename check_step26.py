# -*- coding: utf-8 -*-
"""检查step26数据结构"""
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

# Find step26 files
for date in ['2026-05-03']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    if not os.path.exists(data_dir):
        continue
    for md in sorted(os.listdir(data_dir))[:2]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        s26_path = os.path.join(md_path, 'step26_profit_ratio.json')
        if os.path.exists(s26_path):
            s26 = json.loads(rd(s26_path))
            print(f'=== {md} ===')
            print(f'  analysis: {json.dumps(s26.get("analysis", {}), ensure_ascii=False)}')
            print(f'  profit_data: {json.dumps(s26.get("profit_data", {}), ensure_ascii=False)[:300]}')
            print(f'  profit_ratio: {json.dumps(s26.get("profit_ratio", {}), ensure_ascii=False)[:300]}')
            print()
            break
