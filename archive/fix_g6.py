# -*- coding: utf-8 -*-
"""Fix missing g6 (group06_baijia)"""
import os, glob, json, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

dates = ['2026-05-09', '2026-05-10', '2026-05-12', '2026-05-13']
fixed = 0

for date in dates:
    data_dir = os.path.join(TASKS, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for match_dir in sorted(glob.glob(os.path.join(data_dir, 'match*'))):
        g6 = os.path.join(match_dir, 'group06_baijia')
        if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
            continue  # already has g6
        
        meta_path = os.path.join(match_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        print(f'Fixing g6: {os.path.basename(match_dir)}')
        ret = subprocess.run(
            ['python', 'step8_1923_extractor.py', match_dir],
            capture_output=True, text=True, timeout=120
        )
        if ret.returncode == 0 and os.path.isdir(g6) and len(os.listdir(g6)) > 0:
            fixed += 1
            print(f'  OK')
        else:
            err = ret.stderr[:200] if ret.stderr else 'unknown error'
            print(f'  FAILED ({ret.returncode}): {err[:100]}')

print(f'\nFixed: {fixed}')
