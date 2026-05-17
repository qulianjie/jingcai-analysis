# -*- coding: utf-8 -*-
import os, re

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-02'
counts = {}
files = [f for f in os.listdir(d) if f.endswith('.md') and '周六' in f]

for f in sorted(files):
    fp = os.path.join(d, f)
    content = open(fp, 'r', encoding='utf-8', errors='replace').read()
    m = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
    if m:
        pred = m.group(1).strip()
        counts[pred] = counts.get(pred, 0) + 1

total = sum(counts.values())
print(f'共 {total} 份报告')
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    pct = v / total * 100
    print(f'  {k}: {v} ({pct:.0f}%)')
