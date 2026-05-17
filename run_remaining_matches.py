# -*- coding: utf-8 -*-
"""批量跑剩余比赛分析"""
import os, sys, json, subprocess

SCRIPT_DIR = os.path.dirname(__file__)
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

# 运行 step1-24 分析
scripts = [
    'step146_extractor.py',  # 步骤1,4,6
    'step235_runner.py',     # 步骤2,3,5
    'step7_runner.py',       # 步骤7
    'step8_1923_extractor.py',  # 步骤8,19-23
    'step918_extractor.py',  # 步骤9-18
    'step24_extractor.py',   # 步骤24
    'step25_zhuangjia.py',   # 步骤25
]

date_str = '2026-04-30'
task_dir = os.path.join(TASKS_DIR, date_str)
data_dir = os.path.join(task_dir, 'data')

# 读取比赛列表
with open(os.path.join(task_dir, 'matches_data.json'), 'r', encoding='utf-8') as f:
    matches_data = json.loads(f.read())

matches = matches_data.get('groups', {}).get('周四', {}).get('matches', [])

print(f'=== 跑周四比赛分析 ({len(matches)}场) ===')

for match in matches:
    match_num = match.get('matchnum', '')
    home = match.get('home', '')
    away = match.get('away', '')
    
    # 检查是否已存在
    match_dir_name = f'match{match_num[-3:]}__{home}_{away}'
    match_dir = os.path.join(data_dir, match_dir_name)
    
    if os.path.exists(match_dir):
        print(f'跳过 {match_num} {home}vs{away} (已存在)')
        continue
    
    print(f'\n=== {match_num} {home}vs{away} ===')
    
    # 创建目录
    os.makedirs(match_dir, exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group01_europe'), exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group02_handicap'), exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group03_asian'), exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group04_teamA'), exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group05_teamB'), exist_ok=True)
    os.makedirs(os.path.join(match_dir, 'group06_baijia'), exist_ok=True)
    
    # 创建 meta.json
    meta = {
        'matchnum': match_num,
        'home': home,
        'away': away,
        'fid': match.get('fid', ''),
        'league': match.get('league', ''),
        'time': match.get('time', ''),
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # 跑各步骤
    for script in scripts:
        script_path = os.path.join(SCRIPT_DIR, script)
        if os.path.exists(script_path):
            print(f'  跑 {script}...', end=' ')
            try:
                r = subprocess.run(
                    [sys.executable, script_path, match_dir],
                    capture_output=True, timeout=120,
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                )
                if r.returncode == 0:
                    print('OK')
                else:
                    print(f'FAIL ({r.returncode})')
            except Exception as e:
                print(f'ERROR: {e}')
        else:
            print(f'  跳过 {script} (不存在)')
    
    print(f'  生成报告...')
    # 生成报告
    report_script = os.path.join(SCRIPT_DIR, 'final_report_generator.py')
    report_name = f'{match_num}_{home}vs{away}.md'
    report_path = os.path.join(task_dir, report_name)
    
    try:
        r = subprocess.run(
            [sys.executable, report_script, match_dir, report_path],
            capture_output=True, timeout=60,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        )
        if r.returncode == 0:
            print(f'  OK: {report_name}')
        else:
            print(f'  FAIL: {r.returncode}')
    except Exception as e:
        print(f'  ERROR: {e}')

print('\n完成!')
