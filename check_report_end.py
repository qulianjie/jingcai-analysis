# -*- coding: utf-8 -*-
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        # Find the last 100 lines
        lines = content.split('\n')
        print('=== Last 100 lines ===')
        for line in lines[-100:]:
            print(line[:200])
