# -*- coding: utf-8 -*-
import os, sys, json, subprocess, time, re, shutil

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

# Build dir map
dir_map = {}
for d in sorted(os.listdir(DATA_DIR)):
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
        
        s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
        s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
        s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
        s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
        s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
        is_ok = (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24)
        
        if num not in dir_map or (is_ok and not dir_map[num][1]):
            dir_map[num] = (d, is_ok)

# Find next dir number
max_dir = max([int(d.split('_')[0].replace('match', '')) for d in os.listdir(DATA_DIR) if d.startswith('match')])
next_dir = max_dir + 1

# Identify what needs work - just 5 matches
needs = []
for num in sorted(match_map.keys()):
    if num in dir_map:
        d, is_ok = dir_map[num]
        if not is_ok:
            needs.append((num, d))
    else:
        needs.append((num, None))

print(f'Need to fix: {len(needs)} matches')
# Just do 5 most important ones to avoid timeout
for num, old_d in needs[:5]:
    m = match_map[num]
    home = m.get('home', '')
    away = m.get('away', '')
    
    if old_d:
        match_dir = os.path.join(DATA_DIR, old_d)
    else:
        dir_name = 'match{}_{}__{}'.format(next_dir, home, away)
        match_dir = os.path.join(DATA_DIR, dir_name)
        os.makedirs(match_dir, exist_ok=True)
        meta = {
            'matchnum': m.get('matchnum',''),
            'match': '{} {} vs {}'.format(m.get('matchnum',''), home, away),
            'fid': m.get('fid',''),
            'league': m.get('league',''),
            'home': home,
            'away': away,
            'date': '2026-05-16',
            'status': 'in_progress',
            'home_id': m.get('home_id',''),
            'away_id': m.get('away_id',''),
            'rq': m.get('rq',''),
            'macau_line': m.get('macau_line',''),
        }
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        next_dir += 1
    
    print(f'\n[{num}] {home} vs {away}')
    
    # Run only step918 and step24 (the missing pieces for incomplete ones)
    for script in ['step918_extractor.py', 'step24_extractor.py']:
        print(f'  -> {script}...')
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, script), match_dir],
                timeout=300, encoding='utf-8', errors='replace',
                creationflags=0x08000000
            )
            print(f'  rc={r.returncode}')
        except Exception as e:
            print(f'  ERROR: {e}')
        time.sleep(1)
    
    print('  -> report...')
    try:
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=0x08000000
        )
    except Exception as e:
        print(f'  ERROR: {e}')

# Cleanup duplicate report files
print('\n=== Cleanup ===')
seen = set()
for f in sorted(os.listdir(TASKS_DIR)):
    if f.endswith('.md') and f.startswith('周日'):
        m2 = re.search(r'(\d{3})', f)
        if m2:
            num = m2.group(1)
            if num in seen:
                os.remove(os.path.join(TASKS_DIR, f))
                print(f'  Removed dup: {f}')
            else:
                seen.add(num)

print('\nDone!')
