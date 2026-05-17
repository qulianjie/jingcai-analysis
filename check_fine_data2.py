# -*- coding: utf-8 -*-
"""Check what fine-grained data exists in reports and step files"""
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

# Find a report file
for date in ['2026-05-03']:
    date_dir = os.path.join(TASKS_DIR, date)
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        content = rd(f)
        # Show the full report structure
        lines = content.split('\n')
        for i, line in enumerate(lines[:80]):
            print(f'{i+1}: {line}')
        print('---')
        break

# Check step25 structure for one match
data_dir = os.path.join(TASKS_DIR, '2026-05-03', 'data')
for md in sorted(os.listdir(data_dir)):
    md_path = os.path.join(data_dir, md)
    if not os.path.isdir(md_path):
        continue
    s25 = os.path.join(md_path, 'step25_zhuangjia.json')
    s26 = os.path.join(md_path, 'step26_profit_ratio.json')
    if os.path.exists(s25) and os.path.exists(s26):
        s25d = json.loads(rd(s25))
        s26d = json.loads(rd(s26))
        print(f'\n=== {md} step25 ===')
        print(json.dumps(s25d, ensure_ascii=False, indent=2)[:1000])
        print(f'\n=== {md} step26 ===')
        print(json.dumps(s26d, ensure_ascii=False, indent=2)[:1000])
        break
