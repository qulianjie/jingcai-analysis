# -*- coding: utf-8 -*-
"""Run all pipeline steps for 2026-05-06 matches"""
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

print('Total matches: %d' % len(matches))

steps = [
    'step146_extractor.py',
    'step235_runner.py',
    'step7_runner.py',
    'step8_1923_extractor.py',
    'step918_extractor.py',
    'step24_extractor.py',
]

for idx, match in enumerate(matches, 1):
    home = match.get('home', '')
    away = match.get('away', '')
    fid = match.get('fid', '')
    league = match.get('league', '')
    matchnum = match.get('matchnum', '')
    
    match_dir_name = 'match%d_%s__%s' % (idx, home, away)
    match_dir = os.path.join(TASKS_DIR, 'data', match_dir_name)
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
    
    print('\n=== Match %d: %s vs %s (fid=%s, league=%s) ===' % (idx, home, away, fid, league))
    
    for step_script in steps:
        print('  [%s] ' % step_script, end='', flush=True)
        try:
            result = subprocess.run(
                [sys.executable, os.path.join('C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai', step_script), match_dir],
                capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace'
            )
            if result.returncode == 0:
                print('OK')
            else:
                print('FAIL (rc=%d)' % result.returncode)
                if result.stderr:
                    print('    STDERR:', result.stderr[:500])
        except subprocess.TimeoutExpired:
            print('TIMEOUT')
        except Exception as e:
            print('ERROR: %s' % e)
        time.sleep(1)
    
    time.sleep(2)

print('\n=== All steps complete ===')
