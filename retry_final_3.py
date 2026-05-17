# -*- coding: utf-8 -*-
"""补完match26 + 补跑026, 029, 030"""
import os, sys, json, subprocess, time, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
DATA_DIR = os.path.join(TASKS_DIR, 'data')

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

# First: complete match26 (023) - need step9-18 + step24 + report
print('=== Complete match26 (023) ===')
match26_dirs = [d for d in os.listdir(DATA_DIR) if d.startswith('match26_') and os.path.isdir(os.path.join(DATA_DIR, d))]
if match26_dirs:
    match26_dir = os.path.join(DATA_DIR, match26_dirs[0])
    print(f'Dir: {match26_dirs[0]}')
    
    # Check what's missing
    s9 = os.path.exists(os.path.join(match26_dir, 'group04_teamA', 'step9_home_history.txt'))
    s14 = os.path.exists(os.path.join(match26_dir, 'group05_teamB', 'step14_away_history.txt'))
    s24 = os.path.exists(os.path.join(match26_dir, 'step24_panlu_match.json'))
    
    print(f'  step9: {s9}, step14: {s14}, step24: {s24}')
    
    if not (s9 and s14):
        print('  -> step918_extractor.py...')
        try:
            r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), match26_dir], 
                              timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step918: rc={r.returncode}')
        except Exception as e:
            print(f'  step918: ERROR: {e}')
        time.sleep(2)
    
    if not s24:
        print('  -> step24_extractor.py...')
        try:
            r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step24_extractor.py'), match26_dir], 
                              timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step24: rc={r.returncode}')
        except Exception as e:
            print(f'  step24: ERROR: {e}')
        time.sleep(2)
    
    # Generate report
    print('  -> report...')
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match26_dir],
            timeout=300, encoding='utf-8', errors='replace'
        )
    except Exception as e:
        print(f'  report: ERROR: {e}')

time.sleep(2)

# Remaining: 026, 029, 030
remaining = ['026', '029', '030']
next_dir_num = 27

for num in remaining:
    m = match_map.get(num)
    if not m:
        print(f'MISS {num}: not found')
        continue
    
    home = m.get('home', '')
    away = m.get('away', '')
    match_num = m.get('matchnum', '')
    
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
    
    print(f'\n[{num}] {dir_name}')
    print(f'  league={meta["league"]} fid={meta["fid"]}')
    
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
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            if r.returncode != 0:
                print(f'  {script}: FAIL rc={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  {script}: TIMEOUT')
        except Exception as e:
            print(f'  {script}: ERROR: {e}')
        time.sleep(1)
    
    # Report
    report_path = os.path.join(TASKS_DIR, '{}_{}vs{}.md'.format(match_num, home, away))
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir, report_path],
            timeout=300, encoding='utf-8', errors='replace'
        )
    except:
        pass
    
    next_dir_num += 1
    time.sleep(1)

print('\nDone!')
