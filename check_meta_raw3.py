# -*- coding: utf-8 -*-
import os, json

d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(d)):
    if not os.path.isdir(os.path.join(d, x)):
        continue
    meta_path = os.path.join(d, x, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f'Dir: {x}')
        print(f'  league={repr(meta.get("league", ""))}')
        print(f'  macau_line={repr(meta.get("macau_line", ""))}')
        print(f'  fid={repr(meta.get("fid", ""))}')
        print(f'  home_id={repr(meta.get("home_id", ""))}')
        print(f'  away_id={repr(meta.get("away_id", ""))}')
        break
