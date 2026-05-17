# -*- coding: utf-8 -*-
"""Quick fix for remaining g4/g5/g6"""
import os, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))

# Fix 5/16 match30 g4/g5
match30 = os.path.join(BASE, 'tasks', '2026-05-16', 'data', 'match30_伯恩茅斯__埃弗顿')
print('Fixing match30 g4/g5...')
ret = subprocess.run(['python', 'step918_extractor.py', match30], timeout=180)
g4 = os.path.join(match30, 'group04_teamA')
g5 = os.path.join(match30, 'group05_teamB')
print(f'  g4={os.path.isdir(g4)}, g5={os.path.isdir(g5)}')

# Fix remaining g6
remaining_g6 = [
    ('2026-05-12', 'match8_奥萨苏纳__马竞'),
    ('2026-05-13', 'match5_布雷斯特__斯特拉斯'),
    ('2026-05-13', 'match6_曼彻斯特__纽卡斯尔'),
    ('2026-05-16', 'match28_利物浦__切尔西'),
    ('2026-05-16', 'match30_伯恩茅斯__埃弗顿'),
]

for date, name in remaining_g6:
    match_dir = os.path.join(BASE, 'tasks', date, 'data', name)
    if not os.path.isdir(match_dir):
        print(f'  Not found: {match_dir}')
        continue
    g6 = os.path.join(match_dir, 'group06_baijia')
    if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
        print(f'  {name} g6: already exists')
        continue
    print(f'  Fixing {name} g6...')
    try:
        ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir], timeout=300)
        if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
            print(f'    OK')
        else:
            print(f'    FAIL')
    except Exception as e:
        print(f'    Error: {e}')

# Generate final report for 5/10
print('\nGenerating final report for 5/10...')
try:
    ret = subprocess.run(['python', 'final_report_generator.py', '2026-05-10'], timeout=120)
    print(f'  Exit: {ret.returncode}')
except Exception as e:
    print(f'  Error: {e}')

print('\nDone!')
