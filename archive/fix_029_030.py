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

remaining = ['029', '030']
next_dir_num = 28

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
    
    print(f'[{num}] {dir_name}')
    print(f'  league={meta["league"]} fid={meta["fid"]}')
    
    steps = [
        ('step146_extractor.py', []),
        ('step235_runner.py', []),
        ('step7_runner.py', []),
        ('step8_1923_extractor.py', []),
        ('step918_extractor.py', []),
        ('step24_extractor.py', []),
    ]
    
    for script, extra in steps:
        print(f'  -> {script}...')
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, script), match_dir],
                timeout=1800, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(f'  rc={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  TIMEOUT')
        except Exception as e:
            print(f'  ERROR: {e}')
        time.sleep(1)
    
    # Report
    report_path = os.path.join(TASKS_DIR, '{}_{}vs{}.md'.format(match_num, home, away))
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir, report_path],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f'  report OK')
    except Exception as e:
        print(f'  report ERROR: {e}')
    
    next_dir_num += 1
    time.sleep(1)

print('Done!')
