#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查所有日期数据完整性"""
import os, json, glob

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12','2026-05-13','2026-05-14','2026-05-15']

log_path = os.path.join(SCRIPT_DIR, 'check_all_dates_log.txt')
with open(log_path, 'w', encoding='utf-8') as log:
    for d in dates:
        data_dir = os.path.join(TASKS_DIR, d, 'data')
        root_dir = os.path.join(TASKS_DIR, d)
        if not os.path.isdir(data_dir):
            log.write('{}: NO DATA DIR\n'.format(d))
            continue
        
        tasks = sorted([os.path.basename(d2.rstrip('\\')) for d2 in glob.glob(data_dir + '\\match*\\')])
        
        # 根目录报告
        root_reports = [f for f in os.listdir(root_dir) if f.endswith('.md') and f not in ('sunday_matches.md', 'matches_data.json')]
        
        # 检查各步骤
        has_groups = sum(1 for t in tasks if all(
            os.path.isdir(os.path.join(data_dir, t, g)) for g in 
            ['group01_europe','group02_handicap','group03_asian','group04_teamA','group05_teamB','group06_baijia']
        ))
        has_step24 = sum(1 for t in tasks if os.path.isfile(os.path.join(data_dir, t, 'step24_panlu_match.json')))
        has_step25 = sum(1 for t in tasks if os.path.isfile(os.path.join(data_dir, t, 'step25_zhuangjia.json')))
        has_step26 = sum(1 for t in tasks if os.path.isfile(os.path.join(data_dir, t, 'step26_profit_ratio.json')))
        
        log.write('{}: {} tasks, groups={}/{} step24={}/{} step25={}/{} step26={}/{} reports={}\n'.format(
            d, len(tasks), has_groups, len(tasks), has_step24, len(tasks), has_step25, len(tasks), has_step26, len(tasks), len(root_reports)
        ))
        
        # 记录缺step25/26的
        if has_step25 < len(tasks) or has_step26 < len(tasks):
            log.write('  MISSING step25/26:\n')
            for t in tasks:
                tdir = os.path.join(data_dir, t)
                s25 = os.path.isfile(os.path.join(tdir, 'step25_zhuangjia.json'))
                s26 = os.path.isfile(os.path.join(tdir, 'step26_profit_ratio.json'))
                if not s25 or not s26:
                    log.write('    {}: step25={} step26={}\n'.format(t[:45], s25, s26))

print('Log written to', log_path)
