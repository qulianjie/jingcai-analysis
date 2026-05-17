# -*- coding: utf-8 -*-
"""Check fine-grained data available for pattern matching"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# Check step7/step8 for Macau Asian handicap
for date in ['2026-05-03', '2026-05-04', '2026-05-05']:
    date_dir = os.path.join(TASKS_DIR, date)
    data_dir = os.path.join(date_dir, 'data')
    if not os.path.exists(data_dir):
        continue
    
    # Check step7_macau_same_odds.json
    s7 = os.path.join(data_dir, 'step7_macau_same_odds.json')
    if os.path.exists(s7):
        s7d = json.loads(rd(s7))
        print(f'=== {date} step7 (澳门亚盘同赔) ===')
        if isinstance(s7d, list) and s7d:
            print(f'  First entry keys: {list(s7d[0].keys()) if isinstance(s7d[0], dict) else type(s7d[0])}')
            print(f'  Sample: {json.dumps(s7d[0], ensure_ascii=False)[:300]}')
        elif isinstance(s7d, dict):
            print(f'  Keys: {list(s7d.keys())}')
            print(f'  Sample: {json.dumps(s7d, ensure_ascii=False)[:300]}')
    
    # Check step8
    s8 = os.path.join(data_dir, 'step8_1923.txt')
    if os.path.exists(s8):
        content = rd(s8)
        print(f'\n  === {date} step8 (1923同赔) ===')
        print(f'  First 500 chars: {content[:500]}')
    
    # Check match directories for step6 (亚盘基础)
    count = 0
    for md in sorted(os.listdir(data_dir)):
        if not md.startswith('match') or count >= 2:
            continue
        md_path = os.path.join(data_dir, md)
        s6 = os.path.join(md_path, 'step6_asian_handicap.txt')
        if os.path.exists(s6):
            content = rd(s6)
            print(f'\n  === {md}/step6 (亚盘基础) ===')
            print(f'  {content[:500]}')
            count += 1
        else:
            # List all files
            files = [f for f in os.listdir(md_path) if f.endswith(('.json', '.txt', '.md'))]
            print(f'  {md}: {files}')
