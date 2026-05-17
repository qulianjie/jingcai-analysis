# -*- coding: utf-8 -*-
"""重新生成所有报告（含step25+step26）并同步Notion"""
import os, sys, json, subprocess, time

script_dir = os.path.dirname(__file__)
task_dir = os.path.join(script_dir, 'tasks', '2026-05-10')
data_dir = os.path.join(task_dir, 'data')
gen_script = os.path.join(script_dir, 'final_report_generator.py')

# 找到所有match目录
match_dirs = []
for d in sorted(os.listdir(data_dir)):
    if not d.startswith('match'): continue
    meta_path = os.path.join(data_dir, d, 'meta.json')
    if not os.path.exists(meta_path): continue
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.loads(f.read())
    match_num = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    if not match_num or not home or not away: continue
    report_name = '{}_{}vs{}.md'.format(match_num, home, away)
    report_path = os.path.join(task_dir, report_name)
    match_dirs.append((d, os.path.join(data_dir, d), report_path, match_num))

print('Found {} match directories'.format(len(match_dirs)))

# 生成报告
for dir_name, match_dir, report_path, match_num in match_dirs:
    print('Regenerating {}...'.format(match_num))
    try:
        r = subprocess.run(
            [sys.executable, gen_script, match_dir, report_path],
            capture_output=True, timeout=120
        )
        stdout = r.stdout.decode('utf-8', errors='replace')
        for line in stdout.split('\n'):
            if 'OK:' in line or 'Size:' in line:
                print('  ' + line.strip())
    except Exception as e:
        print('  ERROR: ' + str(e))
    time.sleep(1)

# 同步Notion
print('\n=== Sync to Notion ===')
try:
    r = subprocess.run(
        ['node', os.path.join(script_dir, 'sync_notion.js'), 'add', '2026-05-10'],
        capture_output=True, timeout=300, encoding='utf-8', errors='replace'
    )
    for line in r.stdout.split('\n'):
        if line.strip():
            print('  ' + line.strip()[:100])
except Exception as e:
    print('  ERROR: ' + str(e))

print('\nAll done!')
