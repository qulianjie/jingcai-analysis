# -*- coding: utf-8 -*-
"""Fix 5/16 remaining issues"""
import os, glob, json

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'tasks', '2026-05-16', 'data')

# Fix match30 (empty home_id/away_id)
match30 = None
for d in sorted(glob.glob(os.path.join(DATA_DIR, 'match*'))):
    if 'match30' in d:
        match30 = d
        break

if match30:
    print(f'Fixing: {os.path.basename(match30)}')
    meta_path = os.path.join(match30, 'meta.json')
    meta = json.load(open(meta_path, encoding='utf-8'))
    
    # Update meta with team IDs
    meta['home_id'] = '1205'  # 伯恩茅斯
    meta['away_id'] = '1230'  # 埃弗顿
    meta['macau_line'] = '平手'
    json.dump(meta, open(meta_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'  Updated meta.json')
    
    # Run step918
    print('  Running step918...')
    ret = os.system(f'python step918_extractor.py "{match30}"')
    
    g4 = os.path.isdir(os.path.join(match30, 'group04_teamA'))
    g5 = os.path.isdir(os.path.join(match30, 'group05_teamB'))
    print(f'  g4={g4}, g5={g5}')

# Fix match28 g6
match28 = None
for d in sorted(glob.glob(os.path.join(DATA_DIR, 'match*'))):
    if 'match28' in d:
        match28 = d
        break

if match28:
    print(f'\nFixing: {os.path.basename(match28)}')
    print('  Running step8_1923...')
    ret = os.system(f'python step8_1923_extractor.py "{match28}"')
    g6 = os.path.isdir(os.path.join(match28, 'group06_baijia'))
    print(f'  g6={g6}')

# Generate 5/10 final report
print('\nGenerating 5/10 final report...')
ret = os.system('python final_report_generator.py 2026-05-10')

print('\nDone!')
