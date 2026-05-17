# -*- coding: utf-8 -*-
"""检查meta.json结构"""
import json, os, re

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Check a few meta.json files from different dates
for date_dir in ['2026-04-03', '2026-04-04', '2026-05-03']:
    task_path = os.path.join(TASKS_DIR, date_dir)
    if not os.path.isdir(task_path):
        print('%s: not found' % date_dir)
        continue
    
    print('=== %s ===' % date_dir)
    
    # Check data/match001/meta.json
    meta_path = os.path.join(task_path, 'data', 'match001_大阪樱花vs福冈黄蜂', 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print('Keys: %s' % sorted(meta.keys()))
        if 'match_info' in meta:
            print('match_info keys: %s' % sorted(meta['match_info'].keys()))
            print('match_info.league: %s' % meta['match_info'].get('league', 'NOT FOUND'))
        if 'league' in meta:
            print('meta.league: %s' % meta['league'])
        print('Sample meta (first 500 chars):')
        print(json.dumps(meta, ensure_ascii=False, indent=2)[:500])
    else:
        # Find any meta.json
        data_path = os.path.join(task_path, 'data')
        if os.path.isdir(data_path):
            for subdir in os.listdir(data_path):
                mp = os.path.join(data_path, subdir, 'meta.json')
                if os.path.exists(mp):
                    with open(mp, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    print('Keys: %s' % sorted(meta.keys()))
                    if 'match_info' in meta:
                        print('match_info keys: %s' % sorted(meta['match_info'].keys()))
                        print('match_info.league: %s' % meta['match_info'].get('league', 'NOT FOUND'))
                    if 'league' in meta:
                        print('meta.league: %s' % meta['league'])
                    print('Sample:')
                    print(json.dumps(meta, ensure_ascii=False, indent=2)[:300])
                    break
    
    print()
