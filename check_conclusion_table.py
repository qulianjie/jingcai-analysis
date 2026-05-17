# -*- coding: utf-8 -*-
"""Check what the conclusion summary table looks like"""
import re

report_path = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15/周五001_阿德莱德vs奥克兰FC.md'
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the conclusion section
conclusion_section = re.search(r'# [^#\n\r]+[\s\S]*$', content)
if conclusion_section:
    text = conclusion_section.group(0)
    # Find all table rows with 欧赔趋势, IW同赔, 澳门亚盘 etc
    for line in text.split('\n'):
        if '|' in line and any(k in line for k in ['欧赔', 'IW', '澳门', '主队', '客队', '百家', '欧赔组合', '趋势', '同赔']):
            print(f'MATCH: {line.strip()[:120]}')
    
    # Also print the last 30 lines
    print('\n--- Last 30 lines of conclusion ---')
    lines = text.split('\n')
    for line in lines[-30:]:
        print(f'  {line}')
