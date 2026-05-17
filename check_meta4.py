# -*- coding: utf-8 -*-
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data'
for name in sorted(os.listdir(base)):
    path = os.path.join(base, name)
    if os.path.isdir(path) and 'match4' in name.lower():
        meta_path = os.path.join(path, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            print()
            print(f"league type: {type(meta.get('league'))}")
            print(f"league repr: {repr(meta.get('league'))}")
            print(f"league len: {len(meta.get('league',''))}")
