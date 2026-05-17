# -*- coding: utf-8 -*-
"""Trace extraction end-to-end for 05-03/001"""
import os, json, re, sys

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
fpath = os.path.join(tasks_dir, '2026-05-03', '周日001_大阪樱花vs福冈黄蜂.md')

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

print('=== Step 1: Find dimension signals ===')
dim_pattern = r'\|\s*(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|庄家盈亏)\s*\|\s*([+-]?\d+\.\d+)\s+(利好主|利好客|中立)\s*\|\s*(\d+)%'

dim_map = {
    '欧赔趋势': '欧赔趋势',
    '竞彩同赔': '欧赔趋势',
    'IW同赔': '欧赔趋势',
    '澳门亚盘': '亚盘趋势',
    '让球同赔': '让球趋势',
    '主队主场': '主队主场',
    '客队客场': '客队客场',
    '百家对比': '百家对比',
    '庄家盈亏': '庄家盈亏',
}

combo = {}
for m in re.finditer(dim_pattern, content):
    dim_name = m.group(1)
    score = float(m.group(2))
    direction = m.group(3)
    weight = int(m.group(4))
    
    internal_dim = dim_map.get(dim_name, dim_name)
    combo[f'{internal_dim}_score'] = score
    combo[f'{internal_dim}_dir'] = direction
    combo[f'{internal_dim}_weight'] = weight
    
    print(f'  {dim_name} -> {internal_dim}: score={score}, dir={direction}, weight={weight}')

print(f'\n=== Extracted {len(combo)} combo fields ===')
for k, v in sorted(combo.items()):
    print(f'  {k}: {v}')

# Check if 让球趋势_dir is present
if '让球趋势_dir' in combo:
    print(f'\n✅ 让球趋势_dir = {combo["让球趋势_dir"]}')
else:
    print(f'\n❌ 让球趋势_dir MISSING!')
    
    # Debug: search for 让球同赔 in content
    print('\nSearching for "让球同赔" in report:')
    for i, line in enumerate(content.split('\n')):
        if '让球' in line or '同赔' in line:
            if '利好' in line or '中立' in line:
                print(f'  Line {i+1}: {line.strip()}')
