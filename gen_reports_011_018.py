# -*- coding: utf-8 -*-
"""生成011-018报告 + step25/26 + 同步Notion"""
import os, sys, json, time, subprocess

script_dir = os.path.dirname(__file__)
data_dir = os.path.join(script_dir, 'tasks', '2026-05-10', 'data')
task_dir = os.path.join(script_dir, 'tasks', '2026-05-10')

# 加载比赛列表
matches_file = os.path.join(data_dir, 'matches_data.json')
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.loads(f.read())

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

print('Generating reports for {} matches (011-018)'.format(len(targets)))

# 生成报告
gen_script = os.path.join(script_dir, 'final_report_generator.py')
for match in targets:
    home = match.get('home', '')
    away = match.get('away', '')
    match_no = match.get('matchnum', '')
    
    # 查找对应的match目录
    match_dir = None
    for d in os.listdir(data_dir):
        if d.startswith('match') and home in d and away in d:
            match_dir = os.path.join(data_dir, d)
            break
    
    if match_dir and os.path.exists(match_dir):
        print('Generating report for {}...'.format(match_no))
        try:
            r = subprocess.run(
                [sys.executable, gen_script, match_dir],
                capture_output=True, timeout=120
            )
            stdout = r.stdout.decode('utf-8', errors='replace')
            for line in stdout.split('\n'):
                if 'OK:' in line or 'Size:' in line:
                    print('  ' + line.strip())
        except Exception as e:
            print('  ERROR: ' + str(e))
    else:
        print('  SKIP: {} - dir not found'.format(match_no))
    time.sleep(2)

# Step25
print('\n=== Step25: 庄家盈亏 ===')
try:
    r = subprocess.run(
        [sys.executable, os.path.join(script_dir, 'step25_zhuangjia.py'), '2026-05-10'],
        capture_output=True, text=True, timeout=300,
        encoding='utf-8', errors='replace'
    )
    print('Step25 done')
except Exception as e:
    print('Step25 ERROR: ' + str(e))

# Step26
print('\n=== Step26: 盈亏占比 ===')
try:
    r = subprocess.run(
        [sys.executable, os.path.join(script_dir, 'step26_profit_ratio.py'), '2026-05-10'],
        capture_output=True, text=True, timeout=300,
        encoding='utf-8', errors='replace'
    )
    print('Step26 done')
except Exception as e:
    print('Step26 ERROR: ' + str(e))

# 重新生成报告（含step25/26）
print('\n=== 重新生成报告（含step25/26） ===')
for match in targets:
    home = match.get('home', '')
    away = match.get('away', '')
    match_no = match.get('matchnum', '')
    
    match_dir = None
    for d in os.listdir(data_dir):
        if d.startswith('match') and home in d and away in d:
            match_dir = os.path.join(data_dir, d)
            break
    
    if match_dir and os.path.exists(match_dir):
        print('Regenerating {}...'.format(match_no))
        try:
            r = subprocess.run(
                [sys.executable, gen_script, match_dir],
                capture_output=True, timeout=120
            )
            stdout = r.stdout.decode('utf-8', errors='replace')
            for line in stdout.split('\n'):
                if 'OK:' in line or 'Size:' in line:
                    print('  ' + line.strip())
        except Exception as e:
            print('  ERROR: ' + str(e))
    time.sleep(2)

print('\nAll done!')
