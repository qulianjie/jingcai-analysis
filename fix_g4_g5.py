# -*- coding: utf-8 -*-
"""Fix empty group04/05 files and re-run step918 for affected matches"""
import os, glob, json

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BASE, 'tasks')

dates = ['2026-05-09', '2026-05-10', '2026-05-12', '2026-05-13']
fixed = 0

for date in dates:
    data_dir = os.path.join(TASKS, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for match_dir in sorted(glob.glob(os.path.join(data_dir, 'match*'))):
        meta_path = os.path.join(match_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, encoding='utf-8'))
        g4_dir = os.path.join(match_dir, 'group04_teamA')
        g5_dir = os.path.join(match_dir, 'group05_teamB')
        
        # Check if g4/g5 have files with only headers (no data rows)
        for gdir in [g4_dir, g5_dir]:
            if os.path.isdir(gdir):
                for f in os.listdir(gdir):
                    fpath = os.path.join(gdir, f)
                    size = os.path.getsize(fpath)
                    if size < 500:  # Likely only headers
                        print(f'  Removing empty: {fpath} ({size}B)')
                        os.remove(fpath)
                        fixed += 1
        # Remove empty g4/g5 dirs if no files left
        for gdir in [g4_dir, g5_dir]:
            if os.path.isdir(gdir) and len(os.listdir(gdir)) == 0:
                os.rmdir(gdir)

# Now run step918 for matches missing g4/g5
for date in dates:
    data_dir = os.path.join(TASKS, date, 'data')
    if not os.path.isdir(data_dir):
        continue
    for match_dir in sorted(glob.glob(os.path.join(data_dir, 'match*'))):
        meta_path = os.path.join(match_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        g4 = os.path.join(match_dir, 'group04_teamA')
        g5 = os.path.join(match_dir, 'group05_teamB')
        
        need_g4 = not os.path.isdir(g4) or len(os.listdir(g4)) == 0
        need_g5 = not os.path.isdir(g5) or len(os.listdir(g5)) == 0
        
        if need_g4 or need_g5:
            meta = json.load(open(meta_path, encoding='utf-8'))
            home_id = meta.get('home_id', '')
            away_id = meta.get('away_id', '')
            league = meta.get('league', '')
            fid = meta.get('fid', '')
            macau_line = meta.get('macau_line', '')
            
            g4_file = os.path.join(g4, 'step09_13_teamA.md') if need_g4 else ''
            g5_file = os.path.join(g5, 'step14_18_teamB.md') if need_g5 else ''
            
            cmd = f'python step918_extractor.py "{home_id}" "{away_id}" "{league}" "{fid}" "{macau_line}" "{match_dir}"'
            print(f'Running: {cmd[:80]}...')
            ret = os.system(cmd)
            if ret == 0:
                fixed += 1
                print(f'  OK')
            else:
                print(f'  FAILED (exit={ret})')

print(f'\nTotal fixed: {fixed}')
