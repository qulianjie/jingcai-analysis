# -*- coding: utf-8 -*-
"""并行修复所有剩余问题"""
import os, glob, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

def run_step24(match_dir):
    name = os.path.basename(match_dir)
    step24 = os.path.join(match_dir, 'step24_panlu_match.json')
    if os.path.exists(step24):
        return (name, 'skip', 0)
    ret = subprocess.run(['python', 'step24_extractor.py', match_dir],
                        capture_output=True, text=True, timeout=120)
    return (name, 'OK' if os.path.exists(step24) else 'FAIL', ret.returncode)

def run_g6(match_dir):
    name = os.path.basename(match_dir)
    g6 = os.path.join(match_dir, 'group06_baijia')
    if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
        return (name, 'skip', 0)
    ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir],
                        capture_output=True, text=True, timeout=180)
    return (name, 'OK' if (os.path.isdir(g6) and len(os.listdir(g6)) > 0) else 'FAIL', ret.returncode)

def run_g4g5(match_dir):
    name = os.path.basename(match_dir)
    g4 = os.path.join(match_dir, 'group04_teamA')
    g5 = os.path.join(match_dir, 'group05_teamB')
    need_g4 = not os.path.isdir(g4) or len(os.listdir(g4)) == 0
    need_g5 = not os.path.isdir(g5) or len(os.listdir(g5)) == 0
    if not need_g4 and not need_g5:
        return (name, 'skip', 0)
    ret = subprocess.run(['python', 'step918_extractor.py', match_dir],
                        capture_output=True, text=True, timeout=180)
    g4_ok = os.path.isdir(g4) and len(os.listdir(g4)) > 0
    g5_ok = os.path.isdir(g5) and len(os.listdir(g5)) > 0
    status = 'OK' if (g4_ok and g5_ok) else f'PARTIAL(g4={g4_ok},g5={g5_ok})'
    return (name, status, ret.returncode)

# ============ Step 1: Fix 5/10 step24 ============
print("=" * 60)
print("Step 1: Fix 5/10 step24")
print("=" * 60)
DATA_5_10 = os.path.join(TASKS, '2026-05-10', 'data')
missing_step24 = [os.path.join(DATA_5_10, m) for m in os.listdir(DATA_5_10) 
                  if m.startswith('match') and not os.path.exists(os.path.join(DATA_5_10, m, 'step24_panlu_match.json'))]
print(f'Missing step24: {len(missing_step24)}')
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(run_step24, md) for md in missing_step24]
    for f in as_completed(futures):
        name, status, code = f.result()
        print(f'  {name}: {status} ({code})')

# ============ Step 2: Fix g6 for 5/12 and 5/13 ============
print("\n" + "=" * 60)
print("Step 2: Fix g6 for 5/12 and 5/13")
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
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(run_g6, md) for md in missing_g6]
    for f in as_completed(futures):
        name, status, code = f.result()
        print(f'  {name}: {status} ({code})')

# ============ Step 3: Fix 5/16 ============
print("\n" + "=" * 60)
print("Step 3: Fix 5/16")
print("=" * 60)
DATA_5_16 = os.path.join(TASKS, '2026-05-16', 'data')
for match_dir in sorted(glob.glob(os.path.join(DATA_5_16, 'match*'))):
    g4 = os.path.join(match_dir, 'group04_teamA')
    g5 = os.path.join(match_dir, 'group05_teamB')
    g6 = os.path.join(match_dir, 'group06_baijia')
    name = os.path.basename(match_dir)
    
    need_g4 = not os.path.isdir(g4) or len(os.listdir(g4)) == 0
    need_g5 = not os.path.isdir(g5) or len(os.listdir(g5)) == 0
    need_g6 = not os.path.isdir(g6) or len(os.listdir(g6)) == 0
    
    if need_g4 or need_g5:
        ret = subprocess.run(['python', 'step918_extractor.py', match_dir],
                            capture_output=True, text=True, timeout=180)
        g4_ok = os.path.isdir(g4) and len(os.listdir(g4)) > 0
        g5_ok = os.path.isdir(g5) and len(os.listdir(g5)) > 0
        print(f'  {name} g4/g5: {"OK" if (g4_ok and g5_ok) else "FAIL"}')
    
    if need_g6:
        ret = subprocess.run(['python', 'step8_1923_extractor.py', match_dir],
                            capture_output=True, text=True, timeout=180)
        if os.path.isdir(g6) and len(os.listdir(g6)) > 0:
            print(f'  {name} g6: OK')
        else:
            print(f'  {name} g6: FAIL')

# ============ Step 4: Generate final report for 5/10 ============
print("\n" + "=" * 60)
print("Step 4: Generate final report for 5/10")
print("=" * 60)
try:
    ret = subprocess.run(['python', 'final_report_generator.py', '2026-05-10'],
                        capture_output=True, text=True, timeout=120)
    print(f'  Exit code: {ret.returncode}')
    if ret.stdout:
        for line in ret.stdout.strip().split('\n')[-3:]:
            print(f'    {line}')
except Exception as e:
    print(f'  ERROR: {e}')

print("\n" + "=" * 60)
print("All fixes completed!")
print("=" * 60)
