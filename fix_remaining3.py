# -*- coding: utf-8 -*-
"""Direct fix for remaining issues"""
import os, json, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

# Remaining matches
remaining = [
    ('2026-05-13', 'match5_布雷斯特__斯特拉斯'),
    ('2026-05-13', 'match6_曼彻斯特__纽卡斯尔'),
    ('2026-05-16', 'match28_利物浦__切尔西'),
    ('2026-05-16', 'match30_伯恩茅斯__埃弗顿'),
]

print("Fixing remaining g4/g5/g6...")
for date, name in remaining:
    match_dir = os.path.join(TASKS, date, 'data', name)
    if not os.path.isdir(match_dir):
        print(f'  Not found: {name}')
        continue
    
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
    
    # Check g4/g5
    g4_dir = os.path.join(match_dir, 'group04_teamA')
    g5_dir = os.path.join(match_dir, 'group05_teamB')
    need_g4 = not os.path.isdir(g4_dir) or len(os.listdir(g4_dir)) == 0
    need_g5 = not os.path.isdir(g5_dir) or len(os.listdir(g5_dir)) == 0
    
    if need_g4 or need_g5:
        print(f'  {name}: fixing g4/g5...')
        g4_path = os.path.join(g4_dir, 'step09_13_teamA.md')
        g5_path = os.path.join(g5_dir, 'step14_18_teamB.md')
        os.makedirs(g4_dir, exist_ok=True)
        os.makedirs(g5_dir, exist_ok=True)
        ret = subprocess.run([
            'python', 'step918_extractor.py',
            home_id, away_id, league, fid, macau_line,
            g4_path, g5_path
        ], timeout=180)
        g4_ok = os.path.isdir(g4_dir) and len(os.listdir(g4_dir)) > 0
        g5_ok = os.path.isdir(g5_dir) and len(os.listdir(g5_dir)) > 0
        print(f'    g4={g4_ok}, g5={g5_ok}')
    
    # Fix g6
    g6_dir = os.path.join(match_dir, 'group06_baijia')
    need_g6 = not os.path.isdir(g6_dir) or len(os.listdir(g6_dir)) == 0
    
    if need_g6:
        print(f'  {name}: fixing g6...')
        g6_path = os.path.join(g6_dir, 'step19_baijia_compare.txt')
        ret = subprocess.run([
            'python', 'step8_1923_extractor.py',
            home_id, away_id, league, fid, macau_line,
            '', g6_path
        ], timeout=600)
        if os.path.isdir(g6_dir) and len(os.listdir(g6_dir)) > 0:
            print(f'    OK')
        else:
            print(f'    FAIL')

# Generate 5/10 final report
print("\nGenerating 5/10 final report...")
try:
    ret = subprocess.run(['python', 'final_report_generator.py', '2026-05-10'], timeout=120)
    print(f'  Done (exit={ret.returncode})')
except Exception as e:
    print(f'  Error: {e}')

print("\nDone!")
