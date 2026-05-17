# -*- coding: utf-8 -*-
import os, re

# Check百家对比 format in report
f = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-02\周六001_奥克兰FCvs墨尔本城.md'
content = open(f, 'r', encoding='utf-8', errors='replace').read()

# Find lines containing 百家
lines = [l for l in content.split('\n') if '百家' in l]
print('Lines with 百家:')
for l in lines[:10]:
    safe = l.encode('ascii', errors='replace').decode('ascii')[:120]
    print(f'  {safe}')

# Find lines containing 欧赔 (for odds patterns)
print('\nLines with 欧赔 near 百家:')
idx = content.find('百家')
if idx >= 0:
    snippet = content[max(0,idx-200):idx+500]
    for l in snippet.split('\n'):
        safe = l.encode('ascii', errors='replace').decode('ascii')[:120]
        if '百家' in l or '欧赔' in l or '平均' in l:
            print(f'  {safe}')
