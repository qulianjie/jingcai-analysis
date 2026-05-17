# -*- coding: utf-8 -*-
"""Fix remaining g6 by using match directory path directly"""
import os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

# Find all missing g6
missing = []
for date in ['2026-05-13', '2026-05-16']:
    data_dir = os.path.join(TASKS, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for match_dir in sorted(glob.glob(os.path.join(data_dir, 'match*'))):
        g6_dir = os.path.join(match_dir, 'group06_baijia')
        if not os.path.isdir(g6_dir) or len(os.listdir(g6_dir)) == 0:
            missing.append(match_dir)
            print(f'Missing: {os.path.basename(match_dir)}')

print(f'\nTotal missing: {len(missing)}')

# Fix each one
fixed = 0
for match_dir in missing:
    name = os.path.basename(match_dir)
    print(f'\nFixing: {name}')
    
    # Check g4/g5
    g4_dir = os.path.join(match_dir, 'group04_teamA')
    g5_dir = os.path.join(match_dir, 'group05_teamB')
    need_g4 = not os.path.isdir(g4_dir) or len(os.listdir(g4_dir)) == 0
    need_g5 = not os.path.isdir(g5_dir) or len(os.listdir(g5_dir)) == 0
    
    if need_g4 or need_g5:
        print(f'  Running step918 for g4/g5...')
        os.system(f'python step918_extractor.py "{match_dir}"')
    
    # Fix g6
    print(f'  Running step8_1923 for g6...')
    ret = os.system(f'python step8_1923_extractor.py "{match_dir}"')
    
    g6_dir = os.path.join(match_dir, 'group06_baijia')
    if os.path.isdir(g6_dir) and len(os.listdir(g6_dir)) > 0:
        print(f'  OK')
        fixed += 1
    else:
        print(f'  FAIL')

print(f'\nFixed: {fixed}/{len(missing)}')
