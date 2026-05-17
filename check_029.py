import os, json

DATA_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16\data\match28_纽约红牛__纽约城'
print('Dir exists:', os.path.exists(DATA_DIR))
if os.path.exists(DATA_DIR):
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            rel = os.path.relpath(fp, DATA_DIR)
            print('  {} -> {}B'.format(rel, sz))
