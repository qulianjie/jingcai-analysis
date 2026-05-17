# -*- coding: utf-8 -*-
import os, re

# Check one report
f = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-02\周六011_拜仁vs海登海姆.md'
content = open(f, 'r', encoding='utf-8', errors='replace').read()

# Check if conclusion exists
idx = content.find('最终预测分析')
print(f'File size: {len(content)} chars')
print(f'Has "最终预测分析": {idx}')

# Check for recommendation
m = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
print(f'Has recommendation: {m.group(1).strip() if m else "NO"}')

# Show last 500 chars (safe)
lines = content.split('\n')
print(f'Total lines: {len(lines)}')
print(f'Last 10 lines:')
for l in lines[-10:]:
    safe = l.encode('ascii', errors='replace').decode('ascii')[:100]
    print(f'  {safe}')
