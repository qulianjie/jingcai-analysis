# -*- coding: utf-8 -*-
"""Create missing match directories and run pipeline for them"""
import json, os, sys, time, subprocess

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

TASK_DIR = 'jingcai/tasks/2026-05-09'
DATA_DIR = os.path.join(TASK_DIR, 'data')
SCRIPT_DIR = 'jingcai'

# Load matches
data = json.load(open(os.path.join(TASK_DIR, 'matches_data.json'), 'r', encoding='utf-8'))
sat = data['groups']['周六']['matches']

# Find existing match nums
existing_nums = set()
for d in os.listdir(DATA_DIR):
    if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d)):
        meta_path = os.path.join(DATA_DIR, d, 'meta.json')
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            existing_nums.add(meta.get('matchnum', ''))

# Find missing matches
missing = []
for m in sat:
    mn = m['matchnum']
    if mn not in existing_nums:
        missing.append(m)

print(f'Existing: {len(existing_nums)}, Missing: {len(missing)}')
for m in missing:
    print(f'  {m["matchnum"]}: {m["home"]} vs {m["away"]} (fid={m["fid"]})')

# Run pipeline for each missing match
for i, match in enumerate(missing):
    mn = match['matchnum']
    home = match['home']
    away = match['away']
    fid = match['fid']
    league = match.get('league', '')
    rq = match.get('rq', '')
    
    # Determine match number (1-30)
    match_num = int(mn.replace('周六', ''))
    match_dir_name = f'match{match_num}_{home}__{away}'
    match_dir = os.path.join(DATA_DIR, match_dir_name)
    
    print(f'\n=== [{i+1}/{len(missing)}] Creating {mn}: {home} vs {away} ===')
    os.makedirs(match_dir, exist_ok=True)
    
    # Write meta.json
    meta = {
        'matchnum': mn,
        'match': f'{mn} {home} vs {away}',
        'fid': fid,
        'league': league,
        'home': home,
        'away': away,
        'date': '2026-05-09',
        'status': 'in_progress',
        'home_id': match.get('home_id', ''),
        'away_id': match.get('away_id', ''),
        'rq': rq,
        'macau_line': match.get('macau_line', ''),
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
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
        print(f'  Running {script}...')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, 
                                   encoding='utf-8', errors='replace')
            if result.returncode != 0:
                print(f'  WARN: {script} failed (code {result.returncode})')
                if result.stderr:
                    print(f'  STDERR: {result.stderr[:500]}')
            else:
                print(f'  OK: {script}')
        except subprocess.TimeoutExpired:
            print(f'  TIMEOUT: {script}')
        except Exception as e:
            print(f'  ERROR: {script}: {e}')
        time.sleep(2)
    
    print(f'  Done: {mn}')
    time.sleep(3)

print('\n=== All missing matches processed ===')
