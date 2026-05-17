# -*- coding: utf-8 -*-
import os, sys
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = sys.stdout.buffer
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout, encoding='utf-8', errors='replace')

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        # Find all table rows
        print('=== All table rows ===')
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|') and len(stripped) > 10:
                print(stripped[:200])
