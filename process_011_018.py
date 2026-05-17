# -*- coding: utf-8 -*-
"""处理011-018的比赛"""
import os, sys, json, time, subprocess

TASKS_DIR = os.path.join(os.path.dirname(__file__), 'tasks')
date_str = '2026-05-10'
task_dir = os.path.join(TASKS_DIR, date_str)
data_dir = os.path.join(task_dir, 'data')
script_dir = os.path.dirname(__file__)

# 加载比赛列表
matches_file = os.path.join(data_dir, 'matches_data.json')
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 解析groups格式
groups = data.get('groups', {})
all_matches = []
for gname, gdata in groups.items():
    if isinstance(gdata, dict) and 'matches' in gdata:
        all_matches.extend(gdata['matches'])

# 过滤011-018
targets = []
for m in all_matches:
    no = m.get('matchnum', '')
    import re
    m2 = re.search(r'(\d+)', no)
    if m2:
        num = int(m2.group(1))
        if 11 <= num <= 18:
            targets.append(m)

print('Found {} targets (011-018)'.format(len(targets)))

steps = [
    'step146_extractor.py',
    'step235_runner.py',
    'step7_runner.py',
    'step8_1923_extractor.py',
    'step918_extractor.py',
    'step24_extractor.py',
]

for i, match in enumerate(targets):
    match_no = match.get('matchnum', '周日000')
    home = match.get('home', '')
    away = match.get('away', '')
    match_num_label = '{}'.format(i + 11)
    match_dir_name = 'match{}_{}__{}'.format(match_num_label, home, away)
    match_dir = os.path.join(data_dir, match_dir_name)
    os.makedirs(match_dir, exist_ok=True)
    
    # Write meta.json
    meta = {
        'matchnum': match_no,
        'match': '{} {} vs {}'.format(match_no, home, away),
        'fid': match.get('fid', ''),
        'league': match.get('league', ''),
        'home': home,
        'away': away,
        'date': date_str,
        'status': 'in_progress',
        'home_id': match.get('home_id', ''),
        'away_id': match.get('away_id', ''),
        'rq': match.get('rq', ''),
        'macau_line': match.get('macau_line', ''),
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print('\n=== {} {} vs {} ==='.format(match_no, home, away))
    
    for step_script in steps:
        step_path = os.path.join(script_dir, step_script)
        if not os.path.exists(step_path):
            print('  SKIP: {} not found'.format(step_script))
            continue
        print('  Running {}...'.format(step_script), end=' ')
        try:
            result = subprocess.run(
                [sys.executable, step_path, match_dir],
                capture_output=True, text=True, timeout=600,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            if result.returncode == 0:
                print('OK')
            else:
                print('FAIL: ' + (result.stderr or '')[:100])
        except subprocess.TimeoutExpired:
            print('TIMEOUT')
        except Exception as e:
            print('ERROR: ' + str(e))
        time.sleep(2)
    
    print('  Match {} done!'.format(match_no))
    time.sleep(3)

print('\nAll matches processed!')
print('Now run step25, step26, and report generation...')
