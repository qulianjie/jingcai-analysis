# -*- coding: utf-8 -*-
"""Fix 5/10: run step24 for missing matches"""
import os, glob, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'tasks', '2026-05-10', 'data')

missing = []
for match_dir in sorted(glob.glob(os.path.join(DATA_DIR, 'match*'))):
    step24 = os.path.join(match_dir, 'step24_panlu_match.json')
    if not os.path.exists(step24):
        missing.append(match_dir)

print(f'Missing step24: {len(missing)}')
for match_dir in missing:
    name = os.path.basename(match_dir)
    print(f'Running step24 for {name}...')
    ret = subprocess.run(['python', 'step24_extractor.py', match_dir], 
                        capture_output=True, text=True, timeout=120)
    if os.path.exists(os.path.join(match_dir, 'step24_panlu_match.json')):
        print(f'  OK')
    else:
        print(f'  FAILED ({ret.returncode})')
        if ret.stderr:
            print(f'  Error: {ret.stderr[:200]}')
