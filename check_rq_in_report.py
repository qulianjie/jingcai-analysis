# -*- coding: utf-8 -*-
"""检查报告中让球数据的位置"""
import os, re

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
fpath = os.path.join(tasks_dir, '2026-05-03', '周日001_大阪樱花vs福冈黄蜂.md')

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

print('=== 报告中所有"让球"相关内容 ===')
for i, line in enumerate(content.split('\n'), 1):
    if '让球' in line:
        safe_line = ''.join(c for c in line if ord(c) < 128 or c in '\t')
        print(f'  Line {i}: {safe_line[:100]}')

print('\n=== Step4 让球基础信息 ===')
step4_start = content.find('第4步')
if step4_start > 0:
    section = content[step4_start:step4_start+500]
    for line in section.split('\n')[:20]:
        safe_line = ''.join(c for c in line if ord(c) < 128 or c in '\t')
        print(f'  {safe_line.strip()}')

print('\n=== Step5 让球同赔 ===')
step5_start = content.find('第5步')
if step5_start > 0:
    section = content[step5_start:step5_start+500]
    for line in section.split('\n')[:20]:
        safe_line = ''.join(c for c in line if ord(c) < 128 or c in '\t')
        print(f'  {safe_line.strip()}')

print('\n=== 各维度信号明细表 ===')
dim_start = content.find('各维度信号')
if dim_start > 0:
    section = content[dim_start:dim_start+800]
    for line in section.split('\n'):
        safe = ''.join(c for c in line if ord(c) < 128 or c in '\t')
        print(f'  {safe}')
