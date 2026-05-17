# -*- coding: utf-8 -*-
"""处理017-018"""
import os, sys, json, time, subprocess

script_dir = os.path.dirname(__file__)
data_dir = os.path.join(script_dir, 'tasks', '2026-05-10', 'data')

matches_file = os.path.join(data_dir, 'matches_data.json')
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

groups = data.get('groups', {})
all_matches = []
for gname, gdata in groups.items():
    if isinstance(gdata, dict) and 'matches' in gdata:
        all_matches.extend(gdata['matches'])

targets = []
for m in all_matches:
    no = m.get('matchnum', '')
    import re
    m2 = re.search(r'(\d+)', no)
    if m2:
        num = int(m2.group(1))
        if num >= 17:
            targets.append(m)

steps = ['step146_extractor.py', 'step235_runner.py', 'step7_runner.py',
         'step8_1923_extractor.py', 'step918_extractor.py', 'step24_extractor.py']

for match in targets:
    match_no = match.get('matchnum', '')
    home = match.get('home', '')
    away = match.get('away', '')
    match_dir = os.path.join(data_dir, 'match1_{}__{}'.format(home, away))
    os.makedirs(match_dir, exist_ok=True)
    meta = {'matchnum': match_no, 'match': '{} {} vs {}'.format(match_no, home, away),
            'fid': match.get('fid', ''), 'league': match.get('league', ''),
            'home': home, 'away': away, 'date': '2026-05-10', 'status': 'in_progress',
            'home_id': match.get('home_id', ''), 'away_id': match.get('away_id', ''),
            'rq': match.get('rq', ''), 'macau_line': match.get('macau_line', '')}
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print('=== {} ==='.format(match_no))
    for step in steps:
        step_path = os.path.join(script_dir, step)
        if not os.path.exists(step_path): continue
        print('  {}...'.format(step), end=' ')
        try:
            r = subprocess.run([sys.executable, step_path, match_dir],
                capture_output=True, timeout=600, encoding='utf-8', errors='replace')
            print('OK' if r.returncode == 0 else 'FAIL')
        except: print('ERROR')
        time.sleep(2)
    print('  Done!')
    time.sleep(2)

print('All done!')
