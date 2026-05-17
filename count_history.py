# -*- coding: utf-8 -*-
"""Count historical match directories with key fields"""
import os, json

base = 'jingcai/tasks'
total_matches = 0
total_with_meta = 0
total_with_macau = 0
total_with_fid = 0
total_with_s25 = 0
dates = []

for d in sorted(os.listdir(base)):
    dp = os.path.join(base, d)
    if not os.path.isdir(dp):
        continue
    
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    date_match_count = 0
    date_with_meta = 0
    date_with_macau = 0
    date_with_s25 = 0
    
    for m in os.listdir(data_dir):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp):
            continue
        if not m.startswith('match'):
            continue
        
        date_match_count += 1
        total_matches += 1
        
        meta_path = os.path.join(mp, 'meta.json')
        if os.path.exists(meta_path):
            date_with_meta += 1
            total_with_meta += 1
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            if meta.get('macau_line'):
                date_with_macau += 1
                total_with_macau += 1
            if meta.get('fid'):
                total_with_fid += 1
        
        s25_path = os.path.join(mp, 'step25_zhuangjia.json')
        if os.path.exists(s25_path) and os.path.getsize(s25_path) > 0:
            date_with_s25 += 1
            total_with_s25 += 1
    
    if date_match_count > 0:
        dates.append(f'{d}: {date_match_count}场 (meta:{date_with_meta} macau:{date_with_macau} s25:{date_with_s25})')

print(f'总计: {total_matches}场比赛')
print(f'有meta.json: {total_with_meta}')
print(f'有macau_line: {total_with_macau}')
print(f'有fid: {total_with_fid}')
print(f'有step25: {total_with_s25}')
print(f'缺step25: {total_matches - total_with_s25}')
print()
for dt in dates:
    print(f'  {dt}')
