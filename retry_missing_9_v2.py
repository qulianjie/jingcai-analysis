# -*- coding: utf-8 -*-
"""补跑缺失的9场比赛 - 用正确的目录编号"""
import os, sys, json, subprocess, time, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Missing竞彩编号
missing_nums = ['007', '008', '009', '021', '022', '023', '026', '029', '030']

# Load matches
matches_file = os.path.join(TASKS_DIR, 'matches_data.json')
with open(matches_file, 'r', encoding='utf-8') as f:
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

# Find next available dir number
existing_dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])
max_dir_num = 0
for d in existing_dirs:
    parts = d.split('_', 1)
    num = int(parts[0].replace('match', ''))
    if num > max_dir_num:
        max_dir_num = num

next_dir_num = max_dir_num + 1
print(f'Next dir number: {next_dir_num}')

for num in missing_nums:
    m = match_map.get(num)
    if not m:
        print(f'MISS {num}: not found')
        continue
    
    home = m.get('home', '')
    away = m.get('away', '')
    match_num = m.get('matchnum', '')
    
    # Use next available dir number
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
    
    meta_path = os.path.join(match_dir, 'meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f'\n[{num}] Created: {dir_name}')
    print(f'  league={meta["league"]} fid={meta["fid"]}')
    
    # Run pipeline steps
    steps = [
        ('step146_extractor.py', [match_dir]),
        ('step235_runner.py', [match_dir]),
        ('step7_runner.py', [match_dir]),
        ('step8_1923_extractor.py', [match_dir]),
        ('step918_extractor.py', [match_dir]),
        ('step24_extractor.py', [match_dir]),
    ]
    
    for script, args in steps:
        script_path = os.path.join(SCRIPT_DIR, script)
        cmd = [sys.executable, script_path] + args
        print(f'  -> {script}...')
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            if r.returncode != 0:
                print(f'  {script}: FAIL rc={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  {script}: TIMEOUT')
        except Exception as e:
            print(f'  {script}: ERROR: {e}')
        time.sleep(2)
    
    # Generate report
    report_path = os.path.join(TASKS_DIR, '{}_{}vs{}.md'.format(match_num, home, away))
    print(f'  -> report...')
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir, report_path],
            timeout=300, encoding='utf-8', errors='replace'
        )
        print(f'  Report OK')
    except Exception as e:
        print(f'  Report: ERROR: {e}')
    
    next_dir_num += 1
    time.sleep(2)

print('\nDone!')
