# -*- coding: utf-8 -*-
"""Fix all remaining issues"""
import os, glob, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

# Remaining matches to fix
remaining = [
    os.path.join(TASKS, '2026-05-12', 'data', 'match8_奥萨苏纳__马竞'),
    os.path.join(TASKS, '2026-05-13', 'data', 'match5_布雷斯特__斯特拉斯'),
    os.path.join(TASKS, '2026-05-13', 'data', 'match6_曼彻斯特__纽卡斯尔'),
    os.path.join(TASKS, '2026-05-16', 'data', 'match28_利物浦__切尔西'),
    os.path.join(TASKS, '2026-05-16', 'data', 'match30_伯恩茅斯__埃弗顿'),
]

print("=" * 60)
print("Fixing remaining issues")
print("=" * 60)

for match_dir in remaining:
    if not os.path.isdir(match_dir):
        print(f'Not found: {match_dir}')
        continue
    
    name = os.path.basename(match_dir)
    print(f'\n{name}')
    
    # Fix g4/g5 if missing
    g4 = os.path.join(match_dir, 'group04_teamA')
    g5 = os.path.join(match_dir, 'group05_teamB')
    need_g4 = not os.path.isdir(g4) or len(os.listdir(g4)) == 0
    need_g5 = not os.path.isdir(g5) or len(os.listdir(g5)) == 0
    
    if need_g4 or need_g5:
        print(f'  Running step918 for g4/g5...')
        try:
            ret = subprocess.run(['python', 'step918_extractor.py', match_dir],
                                capture_output=True, text=True, timeout=180)
            g4_ok = os.path.isdir(g4) and len(os.listdir(g4)) > 0
            g5_ok = os.path.isdir(g5) and len(os.listdir(g5)) > 0
            print(f'  g4={g4_ok}, g5={g5_ok}')
        except Exception as e:
            print(f'  Error: {e}')
    
    # Fix g6 if missing
    g6 = os.path.join(match_dir, 'group06_baijia')
    need_g6 = not os.path.isdir(g6) or len(os.listdir(g6)) == 0
    
    if need_g6:
        print(f'  Running step8_1923 for g6...')
        try:
            ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir],
                                capture_output=True, text=True, timeout=300)
            g6_ok = os.path.isdir(g6) and len(os.listdir(g6)) > 0
            print(f'  g6={g6_ok}')
        except Exception as e:
            print(f'  Error: {e}')

# Generate final report for 5/10
print("\n" + "=" * 60)
print("Generating final report for 5/10")
print("=" * 60)
try:
    ret = subprocess.run(['python', 'final_report_generator.py', '2026-05-10'],
                        capture_output=True, text=True, timeout=120)
    print(f'  Exit: {ret.returncode}')
    if ret.stdout:
        for line in ret.stdout.strip().split('\n')[-3:]:
            print(f'    {line}')
except Exception as e:
    print(f'  Error: {e}')

print("\n" + "=" * 60)
print("All fixes completed!")
print("=" * 60)
