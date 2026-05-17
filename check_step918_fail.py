# -*- coding: utf-8 -*-
"""检查 step918 失败原因"""
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
dates = ['2026-05-07','2026-05-08','2026-05-11','2026-05-12','2026-05-13','2026-05-15']

for date in dates:
    data_dir = os.path.join(base, date, 'data')
    if not os.path.exists(data_dir):
        continue
    
    match_dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
    
    for md in match_dirs:
        match_path = os.path.join(data_dir, md)
        meta = json.load(open(os.path.join(match_path, 'meta.json'), encoding='utf-8'))
        
        has_g4 = os.path.exists(os.path.join(match_path, 'group04_teamA'))
        has_g5 = os.path.exists(os.path.join(match_path, 'group05_teamB'))
        
        home_id = meta.get('home_id', '')
        away_id = meta.get('away_id', '')
        league = meta.get('league', '')
        fid = meta.get('fid', '')
        
        if not has_g4 or not has_g5:
            print('{} | {} | home_id={} away_id={} league={} fid={}'.format(
                date, md, home_id, away_id, league, fid))
