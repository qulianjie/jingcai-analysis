# -*- coding: utf-8 -*-
import os, json

# Find match15 directory
d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(d)):
    if not os.path.isdir(os.path.join(d, x)):
        continue
    if 'match15' in x.lower():
        meta_path = os.path.join(d, x, 'meta.json')
        print(f'Dir: {repr(x)}')
        print(f'Meta path: {repr(meta_path)}')
        print(f'Exists: {os.path.exists(meta_path)}')
        
        # Read raw bytes
        with open(meta_path, 'rb') as f:
            raw = f.read()
        print(f'Raw bytes (first 500): {raw[:500]}')
        
        # Parse
        meta = json.loads(raw.decode('utf-8'))
        print(f'Parsed league: {repr(meta.get("league", ""))}')
        print(f'Parsed league bytes: {meta.get("league", "").encode("utf-8")}')
        break
