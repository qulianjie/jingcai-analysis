# -*- coding: utf-8 -*-
import os, sys, json, re, time, subprocess, shutil
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
DATE = '2026-05-16'

os.chdir(SCRIPT_DIR)

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    print('[{}] [{}] {}'.format(t, tag, msg))

def run_script(script_name, args, timeout=3600):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [sys.executable, '-u', script_path] + args
    log('RUN', ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        log('ERROR', '{} RC={}'.format(script_name, result.returncode))
        if result.stderr:
            print('STDERR:', result.stderr[:1000])
        return False
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            log('OUT', line.strip())
    return True

# Step 0 already done
log('STEP', 'Step 0 already done, loading matches...')
matches_path = os.path.join(TASKS_DIR, DATE, 'matches_data.json')
with open(matches_path, 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

# Extract matches
matches = []
for group_name, group_data in matches_data.get('groups', {}).items():
    for m in group_data.get('matches', []):
        seq = m.get('matchnum', '').replace(group_name, '')
        matches.append({
            'seq': seq,
            'matchnum': m.get('matchnum', ''),
            'fid': m.get('fid', ''),
            'home': m.get('home', ''),
            'away': m.get('away', ''),
            'league': m.get('league', ''),
            'time': m.get('time', ''),
            'rq': m.get('rq', -1),
        })

log('INFO', '{} matches found'.format(len(matches)))

# Create match dirs and meta.json for each match
for m in matches:
    seq = m['seq']
    rq = m.get('rq', -1)
    suffix = ''
    if rq == -1:
        suffix = '（非让球）'
    elif rq == 0:
        suffix = '（让球平）'
    elif rq == 1:
        suffix = '（让一球）'
    else:
        suffix = '（让球{}）'.format(rq)
    
    match_name = '{}_{}vs{}'.format(m['matchnum'], m['home'], m['away'])
    match_dir = os.path.join(TASKS_DIR, DATE, match_name)
    
    if not os.path.exists(match_dir):
        os.makedirs(match_dir)
        log('MKDIR', match_name)
    
    # Create group dirs
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
        'rq': rq,
        'match_dir': match_dir,
        'macau_line': '',
        'current_step': 0,
        'status': 'running',
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# Run steps for each match
for idx, m in enumerate(matches):
    seq = m['seq']
    match_name = '{}_{}vs{}'.format(m['matchnum'], m['home'], m['away'])
    match_dir = os.path.join(TASKS_DIR, DATE, match_name)
    
    log('MATCH', '{}/{} {}'.format(idx+1, len(matches), match_name))
    
    # Get home_id and away_id from step1
    if not run_script('step146_extractor.py', [match_dir]):
        log('SKIP', 'step146 failed for {}'.format(match_name))
        continue
    
    # Read meta for home_id/away_id
    meta_path = os.path.join(match_dir, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    league = meta.get('league', '')
    fid = meta.get('fid', '')
    macau_line = meta.get('macau_line', '')
    
    log('META', 'league={}, home_id={}, away_id={}, fid={}'.format(league, home_id, away_id, fid))
    
    if not home_id or not away_id:
        log('SKIP', 'Missing home_id/away_id, skipping match')
        continue
    
    # Step 2: 竞彩同赔
    run_script('step235_runner.py', [home_id, away_id, league, 'jingcai', 'group01_europe/step02_jingcai_same.txt'])
    
    # Step 3: IW同赔
    run_script('step235_runner.py', [home_id, away_id, league, 'interwetten', 'group01_europe/step03_iw_same.txt'])
    
    # Step 5: 让球同赔
    run_script('step235_runner.py', [home_id, away_id, league, 'handicap', 'group02_handicap/step05_handicap_same.txt'])
    
    # Step 7: 澳门亚盘同赔
    run_script('step7_runner.py', [home_id, away_id, league, 'group03_asian/step07_macau_same.txt'])
    
    # Step 8 + 19-23: 同联赛亚盘统计 + 百家对比
    run_script('step8_1923_extractor.py', [match_dir])
    
    # Step 9-18: 主队/客队历史+盘路匹配
    run_script('step918_extractor.py', [home_id, away_id, league, fid, macau_line, match_dir])
    
    # Step 24: 盘路匹配汇总
    run_script('step24_extractor.py', [match_dir])
    
    # Step 25: 庄家盈亏
    run_script('final_audit.js', ['--match', match_dir])
    
    # 生成报告
    run_script('final_conclusion_generator.py', [match_dir])
    run_script('final_report_generator.py', [match_dir])
    
    log('DONE', match_name)
    time.sleep(0.5)

# Generate final report for all matches
log('REPORT', 'Generating combined report...')
run_script('final_stats.py', [DATE])

log('COMPLETE', 'All matches processed')
