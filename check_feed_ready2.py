# -*- coding: utf-8 -*-
import os, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

dates = sorted([d for d in os.listdir(TASKS_DIR)
                if os.path.isdir(os.path.join(TASKS_DIR, d)) and d.count('-') == 2])

done = []
for d in dates:
    if d < '2026-04-03' or d > '2026-04-28':
        continue
    
    task_dir = os.path.join(TASKS_DIR, d)
    items = os.listdir(task_dir)
    
    # Match dirs: matchXXX__name
    match_dirs = [f for f in items if f.startswith('match') and os.path.isdir(os.path.join(task_dir, f))]
    # Reports: xxx001_xxx.md
    reports = [f for f in items if f.endswith('.md')]
    
    if match_dirs and reports:
        done.append((d, len(match_dirs), len(reports)))
        print('OK {}  {} 场 {} 报告'.format(d, len(match_dirs), len(reports)))

print('\n总计: {} 天'.format(len(done)))
if done:
    print('范围: {} ~ {}'.format(done[0][0], done[-1][0]))
