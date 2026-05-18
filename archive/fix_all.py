# -*- coding: utf-8 -*-
import os, sys, json, subprocess, time, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
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

# Build map
dir_map = {}
for d in os.listdir(DATA_DIR):
    if not d.startswith('match') or not os.path.isdir(os.path.join(DATA_DIR, d)):
        continue
    dp = os.path.join(DATA_DIR, d)
    mp = os.path.join(dp, 'meta.json')
    if os.path.exists(mp):
        with open(mp, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        mn = meta.get('matchnum', '')
        n = re.search(r'(\d{3})$', mn)
        if n:
            num = n.group(1)
            s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
            s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
            s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
            s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
            ok = s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0
            if num not in dir_map or (ok and not dir_map[num][1]):
                dir_map[num] = (d, ok)

# Find needs
needs = []
for num in sorted(match_map.keys()):
    if num not in dir_map:
        needs.append(num)
    elif not dir_map[num][1]:
        needs.append(num)

print(f'Needs fix: {needs}')

# Max dir number
max_n = max([int(d.split('_')[0].replace('match','')) for d in os.listdir(DATA_DIR) if d.startswith('match')])
next_n = max_n + 1

# Fix one match at a time
for num in needs[:5]:
    m = match_map[num]
    home = m.get('home', '')
    away = m.get('away', '')
    fid = m.get('fid', '')
    league = m.get('league', '')
    matchnum = m.get('matchnum', '')
    
    if num in dir_map:
        d = dir_map[num][0]
        match_dir = os.path.join(DATA_DIR, d)
    else:
        dn = 'match{}_{}__{}'.format(next_n, home, away)
        match_dir = os.path.join(DATA_DIR, dn)
        os.makedirs(match_dir, exist_ok=True)
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'matchnum': matchnum, 'match': '{} {} vs {}'.format(matchnum, home, away),
                'fid': fid, 'league': league, 'home': home, 'away': away,
                'date': '2026-05-16', 'status': 'in_progress',
                'home_id': m.get('home_id',''), 'away_id': m.get('away_id',''),
                'rq': m.get('rq',''), 'macau_line': m.get('macau_line',''),
            }, f, ensure_ascii=False, indent=2)
        next_n += 1
    
    print(f'\nFixing {num}: {home} vs {away}')
    print(f'Dir: {match_dir}')
    
    # Step 1-6
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step146_extractor.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step146: {p.returncode}')
    time.sleep(1)
    
    # Step 2-3-5
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step235_runner.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step235: {p.returncode}')
    time.sleep(1)
    
    # Step 7
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step7_runner.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step7: {p.returncode}')
    time.sleep(1)
    
    # Step 8+19-23
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step8: {p.returncode}')
    time.sleep(1)
    
    # Step 9-18
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step918: {p.returncode}')
    time.sleep(1)
    
    # Step 24
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'step24_extractor.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  step24: {p.returncode}')
    time.sleep(1)
    
    # Report
    p = subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir],
                        cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait(timeout=300)
    print(f'  report: {p.returncode}')
    
    time.sleep(1)

# Clean up duplicate reports
print('\nCleanup duplicates:')
seen = {}
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and f.startswith('周日'):
        n = re.search(r'(\d{3})', f)
        if n:
            num = n.group(1)
            fp = os.path.join(TASKS_DIR, f)
            if num in seen:
                os.remove(fp)
                print(f'  Removed: {f}')
            else:
                seen[num] = fp

# Final count
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and f.startswith('周日')]
print(f'\nFinal reports: {len(reports)}')
for r in sorted(reports):
    n = re.search(r'(\d{3})', r)
    sz = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {n.group(1) if n else "??"}: {sz:>7}B')
