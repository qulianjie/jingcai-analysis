# -*- coding: utf-8 -*-
import os, re
d = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-02'
counts = {}
for f in os.listdir(d):
    if f.endswith('.md') and '周六' in f:
        content = open(os.path.join(d, f), 'r', encoding='utf-8', errors='replace').read()
        m = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
        if m:
            pred = m.group(1).strip()
            counts[pred] = counts.get(pred, 0) + 1
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'{k}: {v}')
