# -*- coding: utf-8 -*-
"""Fix all remaining issues: step24 for 5/10, g6 for 5/12/5/13, final report for 5/10"""
import os, glob, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

# ============ Fix 1: 5/10 step24 for missing matches ============
print("=" * 60)
print("Fix 1: Running step24 for 5/10 missing matches")
print("=" * 60)
DATA_5_10 = os.path.join(TASKS, '2026-05-10', 'data')
missing_step24 = []
for match_dir in sorted(glob.glob(os.path.join(DATA_5_10, 'match*'))):
    step24 = os.path.join(match_dir, 'step24_panlu_match.json')
    if not os.path.exists(step24):
        missing_step24.append(match_dir)

print(f'Missing step24: {len(missing_step24)}')
for match_dir in missing_step24:
    name = os.path.basename(match_dir)
    print(f'  step24: {name}...', end=' ')
    try:
        ret = subprocess.run(['python', 'step24_extractor.py', match_dir],
                            capture_output=True, text=True, timeout=120)
        if os.path.exists(os.path.join(match_dir, 'step24_panlu_match.json')):
            print('OK')
        else:
            print(f'FAILED ({ret.returncode})')
    except Exception as e:
        print(f'ERROR: {e}')

# ============ Fix 2: g6 for 5/12 and 5/13 ============
print("\n" + "=" * 60)
print("Fix 2: Running step8_1923 for missing g6 matches")
print("=" * 60)
missing_g6 = []
for date in ['2026-05-12', '2026-05-13']:
    data_dir = os.path.join(TASKS, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for match_dir in sorted(glob.glob(os.path.join(data_dir, 'match*'))):
        g6 = os.path.join(match_dir, 'group06_baijia')
        if not os.path.isdir(g6) or len(os.listdir(g6)) == 0:
            missing_g6.append(match_dir)

print(f'Missing g6: {len(missing_g6)}')
for match_dir in missing_g6:
    name = os.path.basename(match_dir)
    print(f'  g6: {name}...', end=' ')
    try:
        ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir],
                            capture_output=True, text=True, timeout=300)
        g6 = os.path.join(match_dir, 'group06_baijia')
        if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
            print('OK')
        else:
            print(f'FAILED ({ret.returncode})')
            if ret.stderr:
                print(f'    Error: {ret.stderr[:100]}')
    except Exception as e:
        print(f'ERROR: {e}')

# ============ Fix 3: 5/16 missing g4/g5/g6 ============
print("\n" + "=" * 60)
print("Fix 3: Running step918/step8_1923 for 5/16 missing")
print("=" * 60)
DATA_5_16 = os.path.join(TASKS, '2026-05-16', 'data')
for match_dir in sorted(glob.glob(os.path.join(DATA_5_16, 'match*'))):
    g4 = os.path.join(match_dir, 'group04_teamA')
    g5 = os.path.join(match_dir, 'group05_teamB')
    g6 = os.path.join(match_dir, 'group06_baijia')
    
    need_g4 = not os.path.isdir(g4) or len(os.listdir(g4)) == 0
    need_g5 = not os.path.isdir(g5) or len(os.listdir(g5)) == 0
    need_g6 = not os.path.isdir(g6) or len(os.listdir(g6)) == 0
    
    if need_g4 or need_g5:
        name = os.path.basename(match_dir)
        print(f'  g4/g5: {name}...', end=' ')
        try:
            ret = subprocess.run(['python', 'step918_extractor.py', match_dir],
                                capture_output=True, text=True, timeout=180)
            g4_ok = os.path.isdir(g4) and len(os.listdir(g4)) > 0
            g5_ok = os.path.isdir(g5) and len(os.listdir(g5)) > 0
            print('OK' if (g4_ok and g5_ok) else f'PARTIAL (g4={g4_ok}, g5={g5_ok})')
        except Exception as e:
            print(f'ERROR: {e}')
    
    if need_g6:
        name = os.path.basename(match_dir)
        print(f'  g6: {name}...', end=' ')
        try:
            ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir],
                                capture_output=True, text=True, timeout=300)
            if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
                print('OK')
            else:
                print(f'FAILED')
        except Exception as e:
            print(f'ERROR: {e}')

# ============ Fix 4: Generate step25 and final report for 5/10 ============
print("\n" + "=" * 60)
print("Fix 4: Running final report generator for 5/10")
print("=" * 60)
try:
    ret = subprocess.run(['python', 'final_report_generator.py', '2026-05-10'],
                        capture_output=True, text=True, timeout=120)
    print(f'  final_report_generator: exit={ret.returncode}')
    if ret.stdout:
        for line in ret.stdout.strip().split('\n')[-5:]:
            print(f'    {line}')
except Exception as e:
    print(f'  ERROR: {e}')

print("\n" + "=" * 60)
print("All fixes completed!")
print("=" * 60)
