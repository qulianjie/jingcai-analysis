# -*- coding: utf-8 -*-
"""Explore fine-grained pattern data"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# 1. Check report header for 澳门亚盘 info
for date in ['2026-05-03']:
    date_dir = os.path.join(TASKS_DIR, date)
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        content = rd(f)
        lines = content.split('\n')[:15]
        for l in lines:
            if '澳门' in l or '亚盘' in l or '让球' in l:
                print(f'{os.path.basename(f)}: {l}')
        break

# 2. Check step6/step7 for Asian handicap data
for date in ['2026-05-03']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    for md in sorted(os.listdir(data_dir))[:3]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        print(f'\n=== {md} ===')
        # Check all json/txt files
        for fname in os.listdir(md_path):
            if fname.endswith('.json'):
                fpath = os.path.join(md_path, fname)
                data = json.loads(rd(fpath))
                print(f'  {fname}: keys={list(data.keys()) if isinstance(data, dict) else "list"}')
                if isinstance(data, dict):
                    if 'data' in data:
                        d = data['data']
                        if isinstance(d, dict):
                            for k, v in list(d.items())[:3]:
                                print(f'    data.{k}: {json.dumps(v, ensure_ascii=False)[:100]}')
                    if 'analysis' in data:
                        print(f'    analysis: {json.dumps(data["analysis"], ensure_ascii=False)[:200]}')
                    if 'conclusion' in data:
                        print(f'    conclusion: {json.dumps(data["conclusion"], ensure_ascii=False)[:100]}')

# 3. Check step8 at date level
for date in ['2026-05-03']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    for fname in os.listdir(data_dir):
        if fname.startswith('step8') or fname.startswith('step7'):
            fpath = os.path.join(data_dir, fname)
            print(f'\n=== data/{fname} ===')
            content = rd(fpath)
            print(content[:500])
    
    # Also check date-level step files
    for fname in os.listdir(os.path.join(TASKS_DIR, date)):
        if fname.startswith('step'):
            fpath = os.path.join(TASKS_DIR, date, fname)
            content = rd(fpath)
            print(f'\n=== {fname} ===')
            print(content[:300])
