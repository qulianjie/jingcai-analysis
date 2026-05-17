# -*- coding: utf-8 -*-
"""Quick test: run step8 for a single match to see debug output"""
import os, json, sys

sys.path.insert(0, 'C:/Users/lianjie/.openclaw/workspace/jingcai')

# Find match15 directory
data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(data_dir)):
    if not os.path.isdir(os.path.join(data_dir, x)):
        continue
    if 'match15' in x.lower():
        match_dir = os.path.join(data_dir, x)
        meta_path = os.path.join(match_dir, 'meta.json')
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f'Match dir: {x}')
        print(f'LEAGUE: {repr(meta.get("league", ""))}')
        print(f'MACAU_LINE: {repr(meta.get("macau_line", ""))}')
        print(f'FID: {repr(meta.get("fid", ""))}')
        print(f'HOME_ID: {repr(meta.get("home_id", ""))}')
        print(f'AWAY_ID: {repr(meta.get("away_id", ""))}')
        
        # Check existing step8 output
        step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(step8_path):
            with open(step8_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = [l for l in content.split('\n') if l.startswith('|')]
            print(f'\nExisting step8: {len(lines)} table rows')
            if content:
                print(f'First 500 chars: {content[:500]}')
        
        # Check step6 for macau line
        step6_path = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
        if os.path.exists(step6_path):
            with open(step6_path, 'r', encoding='utf-8') as f:
                s6 = f.read()
            print(f'\nStep6 content (first 800):')
            print(s6[:800])
        
        break
