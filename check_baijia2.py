# -*- coding: utf-8 -*-
import os, re

f = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-02\周六001_奥克兰FCvs墨尔本城.md'
content = open(f, 'r', encoding='utf-8', errors='replace').read()

# Find the 百家平均 section
lines = content.split('\n')
for i, l in enumerate(lines):
    safe = l.encode('ascii', errors='replace').decode('ascii')[:150]
    if '百家' in l or '平均' in l:
        # Show context
        for j in range(max(0,i-2), min(len(lines), i+5)):
            csafe = lines[j].encode('ascii', errors='replace').decode('ascii')[:150]
            print(f'  [{j}] {csafe}')
        print()
