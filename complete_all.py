# -*- coding: utf-8 -*-
"""补完所有缺失/不完整的竞彩数据"""
import os, sys, json, subprocess, time, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Load matches
with open(os.path.join(TASKS_DIR, 'matches_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

match_map = {}
for m in all_matches:
    num_raw = m.get('matchnum', '')
    m2 = re.search(r'(\d{3})$', num_raw)
    if m2:
        match_map[m2.group(1)] = m

# Build map from match number -> data dir
dir_nums = {}
for d in os.listdir(DATA_DIR):
    if not d.startswith('match') or not os.path.isdir(os.path.join(DATA_DIR, d)):
        continue
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        mn = meta.get('matchnum', '')
        num = ''
        m2 = re.search(r'(\d{3})$', mn)
        if m2:
            num = m2.group(1)
            dir_nums[num] = d

# Find next available dir number
max_dir_num = 0
for d in os.listdir(DATA_DIR):
    if d.startswith('match'):
        num = int(d.split('_')[0].replace('match', ''))
        if num > max_dir_num:
            max_dir_num = num
next_dir_num = max_dir_num + 1

# Identify all that need work
need_work = []

# 1. Missing data dirs (010, 030)
for num in sorted(match_map.keys()):
    if num not in dir_nums:
        need_work.append(('MISSING', num))

# 2. Incomplete data dirs
for num, d in sorted(dir_nums.items()):
    dp = os.path.join(DATA_DIR, d)
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
    s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
    
    if not (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24):
        need_work.append(('INCOMPLETE', num))

print(f'需要补完: {len(need_work)} 场')
for typ, num in need_work:
    m = match_map.get(num, {})
    print(f'  {typ}: {num} - {m.get("home","")} vs {m.get("away","")}')

print(f'\n开始补完...')
time.sleep(2)

# Process each
for typ, num in need_work:
    m = match_map.get(num)
    if not m:
        continue
    
    home = m.get('home', '')
    away = m.get('away', '')
    match_num = m.get('matchnum', '')
    
    if typ == 'MISSING':
        # Create new dir
        dir_name = 'match{}_{}__{}'.format(next_dir_num, home, away)
        match_dir = os.path.join(DATA_DIR, dir_name)
        os.makedirs(match_dir, exist_ok=True)
        
        meta = {
            'matchnum': match_num,
            'match': '{} {} vs {}'.format(match_num, home, away),
            'fid': m.get('fid', ''),
            'league': m.get('league', ''),
            'home': home,
            'away': away,
            'date': '2026-05-16',
            'status': 'in_progress',
            'home_id': m.get('home_id', ''),
            'away_id': m.get('away_id', ''),
            'rq': m.get('rq', ''),
            'macau_line': m.get('macau_line', ''),
        }
        
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        next_dir_num += 1
    
    else:
        # Use existing dir
        d = dir_nums[num]
        match_dir = os.path.join(DATA_DIR, d)
    
    print(f'\n[{num}] {home} vs {away}')
    
    # Run all steps
    steps = [
        'step146_extractor.py',
        'step235_runner.py',
        'step7_runner.py',
        'step8_1923_extractor.py',
        'step918_extractor.py',
        'step24_extractor.py',
    ]
    
    for script in steps:
        print(f'  -> {script}...')
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, script), match_dir],
                timeout=1800, encoding='utf-8', errors='replace',
                creationflags=0x08000000
            )
            print(f'  rc={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  TIMEOUT')
        except Exception as e:
            print(f'  ERROR: {e}')
        time.sleep(1)
    
    # Report
    print('  -> report...')
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=0x08000000
        )
    except Exception as e:
        print(f'  ERROR: {e}')
    
    time.sleep(1)

# Final status
print('\n=== FINAL STATUS ===')
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and f.startswith('周日')]
print(f'报告: {len(reports)} 份')
for r in sorted(reports):
    num = r[2:5]
    size = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {num}: {size:>7}B')
