# -*- coding: utf-8 -*-
import os, json

# Check what match10 directory actually looks like
d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(d)):
    if not os.path.isdir(os.path.join(d, x)):
        continue
    if '弗赖堡' in x or '莱红牛' in x:
        print(f'Found dir: {repr(x)}')
        print(f'Full path: {repr(os.path.join(d, x))}')
        
        meta_path = os.path.join(d, x, 'meta.json')
        print(f'Meta path: {repr(meta_path)}')
        print(f'Meta exists: {os.path.exists(meta_path)}')
        
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f'Meta keys: {list(meta.keys())}')
            print(f'Meta: {json.dumps(meta, ensure_ascii=False, indent=2)}')
        break
