# -*- coding: utf-8 -*-
"""检查 step918 失败原因"""
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12','2026-05-13','2026-05-14','2026-05-15','2026-05-16']

for date in dates:
    data_dir = os.path.join(base, date, 'data')
    if not os.path.exists(data_dir):
        print('{}: no data dir'.format(date))
        continue
    
    match_dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
    total = len(match_dirs)
    g4_count = sum(1 for md in match_dirs if os.path.exists(os.path.join(data_dir, md, 'group04_teamA')))
    g5_count = sum(1 for md in match_dirs if os.path.exists(os.path.join(data_dir, md, 'group05_teamB')))
    
    status = 'OK' if g4_count == total and g5_count == total else 'MISSING {} {}'.format(total-g4_count, total-g5_count)
    print('{}: total={} g4={} g5={} [{}]'.format(date, total, g4_count, g5_count, status))
