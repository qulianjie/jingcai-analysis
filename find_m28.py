import os, sys, json, re

# Try importing the module directly
sys.path.insert(0, r'C:\Users\lianjie\.openclaw\workspace\jingcai')

DATA_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16\data'

# Find match28
for d in os.listdir(DATA_DIR):
    if '纽约红牛' in d:
        print('Found: {}'.format(d))
        dp = os.path.join(DATA_DIR, d)
        
        # Check what exists
        for root, dirs, files in os.walk(dp):
            for f in files:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                rel = os.path.relpath(fp, dp)
                print('  {} -> {}B'.format(rel, sz))
        
        # Check meta
        with open(os.path.join(dp, 'meta.json'), 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print('meta:', json.dumps(meta, ensure_ascii=False))
        break
