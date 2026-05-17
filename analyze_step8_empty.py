# -*- coding: utf-8 -*-
"""分析 step8 空值原因"""
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-13','2026-05-14','2026-05-16']

for date in dates:
    data_dir = os.path.join(base, date, 'data')
    if not os.path.exists(data_dir):
        continue
    
    match_dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
    
    for md in match_dirs:
        match_path = os.path.join(data_dir, md)
        meta = json.load(open(os.path.join(match_path, 'meta.json'), encoding='utf-8'))
        league = meta.get('league', '')
        fid = meta.get('fid', '')
        
        s8 = os.path.join(match_path, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(s8):
            c = open(s8, encoding='utf-8').read().strip()
            if not c or '0场' in c or '提取失败' in c or '筛选结果为0场' in c:
                # 检查 league_id 映射
                try:
                    from league_mapper import load_map
                    jingcai_map = load_map()
                    leagues_file = os.path.join(os.path.dirname(__file__), 'leagues_all.json') if '__file__' in dir() else r'C:\Users\lianjie\.openclaw\workspace\jingcai\leagues_all.json'
                    leagues = json.load(open(leagues_file, encoding='utf-8'))
                    direct = {item['name']: item['id'] for item in leagues}
                    mapped = False
                    for src_name in [league] + jingcai_map.get(league, []):
                        if src_name in direct:
                            mapped = True
                            break
                        for dname in direct:
                            if src_name[:2] in dname or dname[:2] in src_name:
                                mapped = True
                                break
                        if mapped:
                            break
                    status = 'mapped' if mapped else 'NOT_MAPPED'
                except:
                    status = 'check_failed'
                
                print('{} | {} | league={} | fid={} | status={}'.format(date, md, league, fid, status))
