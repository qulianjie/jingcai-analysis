import os, sys, json, subprocess, time

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
import re
for m in all_matches:
    num_raw = m.get('matchnum', '')
    m2 = re.search(r'(\d{3})$', num_raw)
    if m2:
        match_map[m2.group(1)] = m

# Find 029 and 030
for num in ['029', '030']:
    m = match_map.get(num)
    if not m:
        print(f'MISS {num}')
        continue
    
    home = m.get('home', '')
    away = m.get('away', '')
    match_num = m.get('matchnum', '')
    fid = m.get('fid', '')
    league = m.get('league', '')
    
    dir_num = 28 if num == '029' else 29
    
    # Create dir
    dir_name = 'match{}_{}__{}'.format(dir_num, home, away)
    match_dir = os.path.join(DATA_DIR, dir_name)
    os.makedirs(match_dir, exist_ok=True)
    
    meta = {
        'matchnum': match_num,
        'match': '{} {} vs {}'.format(match_num, home, away),
        'fid': fid,
        'league': league,
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
    
    print(f'[{num}] {home} vs {away}')
    print(f'  fid={fid} league={league}')
    print(f'  dir={dir_name}')
    
    # Run step146
    print('  -> step146...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step146_extractor.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step146 ERROR: {e}')
    time.sleep(1)
    
    # Run step235
    print('  -> step235...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step235_runner.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step235 ERROR: {e}')
    time.sleep(1)
    
    # Run step7
    print('  -> step7...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step7_runner.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step7 ERROR: {e}')
    time.sleep(1)
    
    # Run step8+19-23
    print('  -> step8...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step8 ERROR: {e}')
    time.sleep(1)
    
    # Run step9-18
    print('  -> step9-18...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step9-18 ERROR: {e}')
    time.sleep(1)
    
    # Run step24
    print('  -> step24...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'step24_extractor.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  step24 ERROR: {e}')
    time.sleep(1)
    
    # Report
    print('  -> report...')
    try:
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir],
                      timeout=300, creationflags=0x08000000)
    except Exception as e:
        print(f'  report ERROR: {e}')
    
    time.sleep(1)

# Final status
print('\n=== STATUS ===')
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and f.startswith('周日')]
print(f'Reports: {len(reports)}')
for r in sorted(reports):
    size = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {r[:40]:40s} {size}B')
