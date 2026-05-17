# -*- coding: utf-8 -*-
"""批量重新生成报告（含自动预测结论）"""
import os, sys, json, subprocess

SCRIPT = os.path.join(os.path.dirname(__file__), 'final_report_generator.py')
TASKS_DIR = os.path.join(os.path.dirname(__file__), 'tasks')

dates = ['2026-04-29', '2026-04-30']
total = 0
success = 0

for date in dates:
    task_dir = os.path.join(TASKS_DIR, date)
    data_dir = os.path.join(task_dir, 'data')
    if not os.path.exists(data_dir):
        print(f'[{date}] data目录不存在，跳过')
        continue

    for d in sorted(os.listdir(data_dir)):
        if not d.startswith('match') or not os.path.isdir(os.path.join(data_dir, d)):
            continue

        match_dir = os.path.join(data_dir, d)
        
        # 读取meta.json获取正确的matchnum
        meta_path = os.path.join(match_dir, 'meta.json')
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.loads(f.read())
        except:
            meta = {}
        
        match_num = meta.get('matchnum', '')
        if not match_num:
            match_num = d.split('__')[0].replace('match', '')
        
        # 从match_name提取teams部分
        match_name = meta.get('match_name', '')
        if '_' in match_name:
            teams = match_name.split('_', 1)[1]
        else:
            teams = d.split('__', 1)[1].replace('_', '') if '__' in d else d
        teams_clean = teams.replace(' vs ', 'vs').replace('VS', 'vs')
        
        report_path = os.path.join(task_dir, '{}_{}.md'.format(match_num, teams_clean))

        total += 1
        print(f'[{date}] {d} -> {os.path.basename(report_path)}...', end=' ')
        try:
            r = subprocess.run(
                [sys.executable, SCRIPT, match_dir, report_path],
                capture_output=True, timeout=60,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            )
            if r.returncode == 0:
                size = os.path.getsize(report_path)
                print(f'OK ({size} bytes)')
                success += 1
            else:
                err = r.stderr.decode('utf-8', errors='replace')[:200]
                print(f'FAIL: {err}')
        except Exception as e:
            print(f'ERROR: {e}')

print(f'\n完成: {success}/{total} 成功')
