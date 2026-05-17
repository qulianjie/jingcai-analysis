# -*- coding: utf-8 -*-
"""Check what the conclusion summary table looks like"""
import re

report_path = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/周五001_阿德莱德vs奥克兰FC.md'
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find lines containing dimension scores
for i, line in enumerate(content.split('\n')):
    if '|' in line and any(k in line for k in ['欧赔趋势', 'IW同赔', '澳门亚盘', '主队主场', '客队客场', '百家对比', '欧赔组合']):
        with open('C:/Users/lianjie/.openclaw/workspace/jingcai/conclusion_table.txt', 'a', encoding='utf-8') as f:
            f.write(f'LINE {i}: {line.strip()}\n')

print('Done - wrote to conclusion_table.txt')
