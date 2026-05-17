# -*- coding: utf-8 -*-
"""Continue pipeline for 2026-05-06 - remaining matches and steps"""
import sys, os, json, time, subprocess

os.chdir(r'C:\Users\lianjie\.openclaw\workspace\jingcai')
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-06'
DATE = '2026-05-06'

# Load matches
with open(os.path.join(TASKS_DIR, 'matches_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = []
for gn, gd in data.get('groups', {}).items():
    for m in gd.get('matches', []):
        matches.append(m)

# Steps that need to run per match
steps = [
    ('step146_extractor.py', 60),
    ('step235_runner.py', 60),
    ('step7_runner.py', 60),
    ('step8_1923_extractor.py', 180),  # increased timeout
    ('step918_extractor.py', 120),
    ('step24_extractor.py', 120),
]

# Check which matches need processing
for idx, match in enumerate(matches, 1):
    home = match.get('home', '')
    away = match.get('away', '')
    fid = match.get('fid', '')
    league = match.get('league', '')
    matchnum = match.get('matchnum', '')
    
    match_dir_name = 'match%d_%s__%s' % (idx, home, away)
    match_dir = os.path.join(TASKS_DIR, 'data', match_dir_name)
    
    # Check what's already done
    needed_files = {
        'step146': ['group01_europe/step1_europe_base.txt', 'group02_handicap/step4_handicap_base.txt', 'group03_asian/step6_asian_base.txt'],
        'step235': ['group01_europe/step2_jingcai_same.txt', 'group01_europe/step3_interwetten_same.txt', 'group02_handicap/step5_handicap_same.txt'],
        'step7': ['group03_asian/step7_macau_same.txt'],
        'step8': ['group03_asian/step8_same_league.txt'],
        'step918': ['group04_teamA/step9_home_history.txt', 'group05_teamB/step14_away_history.txt'],
        'step24': ['step24_panlu_match.json'],
    }
    
    missing = []
    for step_name, files in needed_files.items():
        for f in files:
            if not os.path.exists(os.path.join(match_dir, f)):
                missing.append(step_name)
                break
    
    if not missing:
        print('Match %d (%s vs %s): ALREADY COMPLETE' % (idx, home, away))
        continue
    
    print('\n=== Match %d: %s vs %s (fid=%s) ===' % (idx, home, away, fid))
    print('  Missing steps: %s' % ', '.join(missing))
    
    # Create dir if needed
    os.makedirs(match_dir, exist_ok=True)
    
    # Write meta.json
    meta = {
        'matchnum': matchnum,
        'match': '%s %s vs %s' % (matchnum, home, away),
        'fid': fid,
        'league': league,
        'home': home,
        'away': away,
        'date': DATE,
        'status': 'in_progress',
        'home_id': match.get('home_id', ''),
        'away_id': match.get('away_id', ''),
        'rq': match.get('rq', ''),
        'macau_line': match.get('macau_line', ''),
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # Run only missing steps
    for step_script, timeout in steps:
        if step_script.replace('step', '').replace('_runner.py', '').replace('_extractor.py', '') not in missing:
            # More flexible matching
            step_key = step_script.split('_')[0].replace('step', '')
            if step_key not in ['146', '235', '7', '81923', '918', '24']:
                continue
            # Map script to needed step
            script_to_step = {
                'step146_extractor.py': 'step146',
                'step235_runner.py': 'step235',
                'step7_runner.py': 'step7',
                'step8_1923_extractor.py': 'step8',
                'step918_extractor.py': 'step918',
                'step24_extractor.py': 'step24',
            }
            if script_to_step.get(step_script) not in missing:
                continue
        
        print('  [%s] ' % step_script, end='', flush=True)
        try:
            result = subprocess.run(
                [sys.executable, os.path.join('C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai', step_script), match_dir],
                capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                print('OK')
            else:
                print('FAIL (rc=%d)' % result.returncode)
                if result.stderr:
                    for line in result.stderr.strip().split('\n')[-3:]:
                        print('    ', line.strip()[:200])
        except subprocess.TimeoutExpired:
            print('TIMEOUT (%ds)' % timeout)
        except Exception as e:
            print('ERROR: %s' % e)
        time.sleep(1)
    
    time.sleep(2)

print('\n=== All remaining steps complete ===')
