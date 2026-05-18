# -*- coding: utf-8 -*-
"""Final fix for remaining 5/16 issues"""
import os, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'tasks', '2026-05-16', 'data')

# Find all missing g4/g5/g6
missing = []
for match_dir in sorted(glob.glob(os.path.join(DATA_DIR, 'match*'))):
    g4 = os.path.isdir(os.path.join(match_dir, 'group04_teamA')) and len(os.listdir(os.path.join(match_dir, 'group04_teamA'))) > 0
    g5 = os.path.isdir(os.path.join(match_dir, 'group05_teamB')) and len(os.listdir(os.path.join(match_dir, 'group05_teamB'))) > 0
    g6 = os.path.isdir(os.path.join(match_dir, 'group06_baijia')) and len(os.listdir(os.path.join(match_dir, 'group06_baijia'))) > 0
    
    if not g4 or not g5 or not g6:
        flags = []
        if not g4: flags.append('g4')
        if not g5: flags.append('g5')
        if not g6: flags.append('g6')
        missing.append((match_dir, flags))
        print(f'Missing: {os.path.basename(match_dir)} - {", ".join(flags)}')

print(f'\nTotal missing: {len(missing)}')

# Fix each one
for match_dir, flags in missing:
    name = os.path.basename(match_dir)
    meta_path = os.path.join(match_dir, 'meta.json')
    if not os.path.exists(meta_path):
        print(f'  {name}: no meta.json')
        continue
    
    meta = json.load(open(meta_path, encoding='utf-8'))
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    league = meta.get('league', '')
    fid = meta.get('fid', '')
    macau_line = meta.get('macau_line', '')
    
    if 'g4' in flags or 'g5' in flags:
        print(f'  {name}: fixing g4/g5...')
        ret = os.system(f'python step918_extractor.py "{match_dir}"')
    
    if 'g6' in flags:
        print(f'  {name}: fixing g6...')
        ret = os.system(f'python step8_1923_extractor.py "{match_dir}"')

# Verify
print('\nFinal verification:')
for match_dir, flags in missing:
    name = os.path.basename(match_dir)
    g4 = os.path.isdir(os.path.join(match_dir, 'group04_teamA')) and len(os.listdir(os.path.join(match_dir, 'group04_teamA'))) > 0
    g5 = os.path.isdir(os.path.join(match_dir, 'group05_teamB')) and len(os.listdir(os.path.join(match_dir, 'group05_teamB'))) > 0
    g6 = os.path.isdir(os.path.join(match_dir, 'group06_baijia')) and len(os.listdir(os.path.join(match_dir, 'group06_baijia'))) > 0
    print(f'  {name}: g4={g4} g5={g5} g6={g6}')
