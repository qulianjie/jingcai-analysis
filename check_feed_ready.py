# -*- coding: utf-8 -*-
import os, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

dates = sorted([d for d in os.listdir(TASKS_DIR)
                if os.path.isdir(os.path.join(TASKS_DIR, d)) and d.count('-') == 2])

pending = []
done = []
for d in dates:
    if d < '2026-04-03' or d > '2026-04-28':
        continue
    
    task_dir = os.path.join(TASKS_DIR, d)
    data_dir = os.path.join(task_dir, 'data')
    
    # Check if has any match dirs
    if not os.path.exists(data_dir):
        pending.append(d)
        continue
    
    matches = [f for f in os.listdir(data_dir) if f.startswith('match')]
    if not matches:
        pending.append(d)
        continue
    
    # Check if all matches have reports
    all_done = True
    for m in matches:
        # Check report exists
        report_name = m.replace('_', '')
        report_path = os.path.join(task_dir, '{}.md'.format(report_name))
        if not os.path.exists(report_path):
            all_done = False
            break
    
    if all_done:
        done.append(d)
    else:
        pending.append(d)

print('04-03 ~ 04-28 已完成日期:')
for d in done:
    task_dir = os.path.join(TASKS_DIR, d)
    data_dir = os.path.join(task_dir, 'data')
    matches = [f for f in os.listdir(data_dir) if f.startswith('match')]
    reports = [f for f in os.listdir(task_dir) if f.endswith('.md')]
    print('  {}  {} 场完成  {} 个报告'.format(d, len(matches), len(reports)))

print('\n未完成日期:')
for d in pending:
    print('  {}'.format(d))

# Generate feed command
if done:
    date_range = '{} -- {}'.format(done[0], done[-1])
    print('\n--dates \"{} -- {}\"'.format(done[0], done[-1]))
    print('\n日期列表:')
    print(' '.join(done))
