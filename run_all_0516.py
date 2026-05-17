# -*- coding: utf-8 -*-
"""Run all steps for all 30 matches of 2026-05-16"""
import os, sys, json, subprocess, time
from datetime import datetime

os.chdir('C:/Users/lianjie/.openclaw/workspace/jingcai')
os.environ['PYTHONIOENCODING'] = 'utf-8'

DATE = '2026-05-16'
TASKS_DIR = 'tasks/{}'.format(DATE)

# Load matches
with open('{}/matches_data.json'.format(TASKS_DIR), 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

matches = []
for group_name, group_data in matches_data.get('groups', {}).items():
    for m in group_data.get('matches', []):
        matches.append({
            'matchnum': m.get('matchnum', ''),
            'fid': m.get('fid', ''),
            'home': m.get('home', ''),
            'away': m.get('away', ''),
            'league': m.get('league', ''),
            'time': m.get('time', ''),
            'rq': m.get('rq', -1),
        })

print('[INFO] {} matches found'.format(len(matches)))

# Create match dirs and meta.json
for m in matches:
    match_name = '{}_{}vs{}'.format(m['matchnum'], m['home'], m['away'])
    match_dir = os.path.join(TASKS_DIR, match_name)
    
    if not os.path.exists(match_dir):
        os.makedirs(match_dir)
    
    for g in ['group01_europe', 'group02_handicap', 'group03_asian', 'group04_teamA', 'group05_teamB', 'group06_baijia']:
        os.makedirs(os.path.join(match_dir, g), exist_ok=True)
    
    meta = {
        'matchnum': m['matchnum'],
        'date': DATE,
        'league': m['league'],
        'home': m['home'],
        'away': m['away'],
        'time': m['time'],
        'fid': m['fid'],
        'rq': m.get('rq', -1),
        'match_dir': match_dir,
        'macau_line': '',
        'current_step': 0,
        'status': 'running',
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# Process each match
for idx, m in enumerate(matches):
    match_name = '{}_{}vs{}'.format(m['matchnum'], m['home'], m['away'])
    match_dir = os.path.join(TASKS_DIR, match_name)
    
    print('\n[{}] {}/{}'.format(datetime.now().strftime('%H:%M:%S'), idx+1, len(matches)))
    print('[MATCH] {}'.format(match_name))
    
    # Step 146
    ret = os.system('python step146_extractor.py "{}"'.format(match_dir))
    if ret != 0:
        print('[SKIP] step146 failed')
        continue
    
    # Read meta
    with open(os.path.join(match_dir, 'meta.json'), 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    league = meta.get('league', '')
    fid = meta.get('fid', '')
    macau_line = meta.get('macau_line', '')
    
    if not home_id or not away_id:
        print('[SKIP] Missing home_id/away_id')
        continue
    
    print('[META] league={}, home_id={}, away_id={}'.format(league, home_id, away_id))
    
    # Step 2: 竞彩同赔
    ret = os.system('python step235_runner.py {} {} jingcai group01_europe/step02_jingcai_same.txt'.format(home_id, away_id))
    print('[STEP2] RC={}'.format(ret))
    
    # Step 3: IW同赔
    ret = os.system('python step235_runner.py {} {} interwetten group01_europe/step03_iw_same.txt'.format(home_id, away_id))
    print('[STEP3] RC={}'.format(ret))
    
    # Step 5: 让球同赔
    ret = os.system('python step235_runner.py {} {} handicap group02_handicap/step05_handicap_same.txt'.format(home_id, away_id))
    print('[STEP5] RC={}'.format(ret))
    
    # Step 7: 澳门亚盘同赔
    ret = os.system('python step7_runner.py {} {} {} group03_asian/step07_macau_same.txt'.format(home_id, away_id, league))
    print('[STEP7] RC={}'.format(ret))
    
    # Step 8 + 19-23
    ret = os.system('python step8_1923_extractor.py "{}"'.format(match_dir))
    print('[STEP8+19-23] RC={}'.format(ret))
    
    # Step 9-18
    ret = os.system('python step918_extractor.py {} {} {} {} "{}" "{}"'.format(home_id, away_id, league, fid, macau_line, match_dir))
    print('[STEP9-18] RC={}'.format(ret))
    
    # Step 24
    ret = os.system('python step24_extractor.py "{}"'.format(match_dir))
    print('[STEP24] RC={}'.format(ret))
    
    # Final conclusion
    ret = os.system('python final_conclusion_generator.py "{}"'.format(match_dir))
    print('[CONCLUSION] RC={}'.format(ret))
    
    # Final report
    ret = os.system('python final_report_generator.py "{}"'.format(match_dir))
    print('[REPORT] RC={}'.format(ret))
    
    # Check step8 and step19
    step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
    step19_path = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')
    
    s8_size = os.path.getsize(step8_path) if os.path.exists(step8_path) else 0
    s19_size = os.path.getsize(step19_path) if os.path.exists(step19_path) else 0
    
    print('[CHECK] step8={}B, step19={}B'.format(s8_size, s19_size))
    if s8_size == 0 or s19_size == 0:
        print('[WARN] Empty data!')
    
    time.sleep(0.5)

print('\n[DONE] All matches processed')
