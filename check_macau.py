# -*- coding: utf-8 -*-
import os, re, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

task_dir = 'C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai\\tasks\\2026-05-12'
files = [f for f in os.listdir(task_dir) if f.endswith('.md') and 'sunday' not in f.lower()]
files.sort()

for f in files[:8]:
    path = os.path.join(task_dir, f)
    content = open(path, 'r', encoding='utf-8').read()
    # Find the last section with trend summary
    # Look for lines with 亚盘同赔 or 澳门亚盘 trend
    lines = [l.strip() for l in content.split('\n') if '亚盘' in l and ('利好' in l or '同赔' in l)]
    print(f'=== {f} ===')
    for l in lines[-5:]:
        print(f'  {l}')
    print()
