# -*- coding: utf-8 -*-
import os, json

data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'

# Check step8 output for match1 (日职)
x = 'match1'
for d in sorted(os.listdir(data_dir)):
    if d.startswith(x + '_'):
        match_dir = os.path.join(data_dir, d)
        
        meta_path = os.path.join(match_dir, 'meta.json')
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        print(f'Dir: {d}')
        print(f'  league: {repr(meta.get("league", ""))}')
        print(f'  macau_line: {repr(meta.get("macau_line", ""))}')
        print(f'  fid: {repr(meta.get("fid", ""))}')
        print(f'  home_id: {repr(meta.get("home_id", ""))}')
        print(f'  away_id: {repr(meta.get("away_id", ""))}')
        
        # Check step6 for macau line
        step6_path = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
        if os.path.exists(step6_path):
            with open(step6_path, 'r', encoding='utf-8') as f:
                s6 = f.read()
            print(f'\n  Step6 content:')
            for line in s6.split('\n')[:15]:
                if line.strip():
                    print(f'    {line}')
        
        # Check step8 output
        step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
        if os.path.exists(step8_path):
            with open(step8_path, 'r', encoding='utf-8') as f:
                s8 = f.read()
            print(f'\n  Step8 content (first 800):')
            for line in s8.split('\n')[:20]:
                if line.strip():
                    print(f'    {line}')
        
        break
