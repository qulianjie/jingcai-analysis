# -*- coding: utf-8 -*-
import os, json, sys

# Find match15 directory
d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(d)):
    if not os.path.isdir(os.path.join(d, x)):
        continue
    if 'match15' in x.lower():
        match_dir = os.path.join(d, x)
        meta_path = os.path.join(match_dir, 'meta.json')
        
        print(f'Match dir: {repr(match_dir)}')
        print(f'Meta path: {repr(meta_path)}')
        print(f'Meta exists: {os.path.exists(meta_path)}')
        
        # Simulate what step8_1923_extractor.py does
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            HOME_ID = meta.get('home_id', '')
            AWAY_ID = meta.get('away_id', '')
            LEAGUE = meta.get('league', '')
            FID = meta.get('fid', '')
            MACAU_LINE = meta.get('macau_line', '')
            
            print(f'HOME_ID: {repr(HOME_ID)}')
            print(f'AWAY_ID: {repr(AWAY_ID)}')
            print(f'LEAGUE: {repr(LEAGUE)}')
            print(f'FID: {repr(FID)}')
            print(f'MACAU_LINE: {repr(MACAU_LINE)}')
        break
