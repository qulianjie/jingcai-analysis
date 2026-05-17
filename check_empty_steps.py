# -*- coding: utf-8 -*-
"""检查 step8 和 step19 空值问题"""
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12','2026-05-13','2026-05-14','2026-05-15','2026-05-16']

for date in dates:
    data_dir = os.path.join(base, date, 'data')
    if not os.path.exists(data_dir):
        print('{}: no data dir'.format(date))
        continue
    
    match_dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
    s8_empty = 0
    s19_empty = 0
    total = len(match_dirs)
    
    for md in match_dirs:
        match_path = os.path.join(data_dir, md)
        meta = json.load(open(os.path.join(match_path, 'meta.json'), encoding='utf-8'))
        league = meta.get('league', '')
        
        # check step8
        s8 = os.path.join(match_path, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(s8):
            c = open(s8, encoding='utf-8').read().strip()
            if not c or '0场' in c or '提取失败' in c or '筛选结果为0场' in c:
                s8_empty += 1
        
        # check step19
        s19 = os.path.join(match_path, 'group06_baijia', 'step19_baijia_compare.txt')
        if os.path.exists(s19):
            c = open(s19, encoding='utf-8').read().strip()
            if not c or '提取失败' in c or '无数据' in c:
                s19_empty += 1
    
    print('{}: total={} s8_empty={} s19_empty={}'.format(date, total, s8_empty, s19_empty))
