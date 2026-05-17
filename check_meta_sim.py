# -*- coding: utf-8 -*-
import os, json, sys

# Simulate exact step8_1923_extractor.py logic
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    MATCH_DIR = sys.argv[1]
    meta_path = os.path.join(MATCH_DIR, 'meta.json')
    print(f'MATCH_DIR: {repr(MATCH_DIR)}')
    print(f'Meta path: {repr(meta_path)}')
    print(f'Meta exists: {os.path.exists(meta_path)}')
    
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
else:
    print(f'ARGV[1] is not a directory: {repr(sys.argv[1])}')
