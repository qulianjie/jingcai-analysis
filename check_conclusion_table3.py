# -*- coding: utf-8 -*-
"""Check conclusion summary table for all 05-15 reports"""
import os, re

tasks_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-15'
reports = [f for f in os.listdir(tasks_dir) if f.endswith('.md') and f != 'sunday_matches.md']

for report in sorted(reports):
    path = os.path.join(tasks_dir, report)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find lines containing dimension scores in conclusion section
    conclusion = re.search(r'# 第九部分[\s\S]*$', content)
    if not conclusion:
        conclusion = re.search(r'# [^#\n\r]*(?:最终|结论)[^#\n\r]*[\s\S]*$', content, re.I)
    if not conclusion:
        conclusion_text = content[-2000:]
    else:
        conclusion_text = conclusion.group(0)
    
    labels = ['欧赔趋势', 'IW同赔', '澳门亚盘', '主队主场', '客队客场', '百家对比', '欧赔组合']
    found = {}
    for line in conclusion_text.split('\n'):
        if '|' not in line:
            continue
        for label in labels:
            if label in line and '---' not in line:
                found[label] = line.strip()[:100]
    
    missing = [l for l in labels if l not in found]
    if missing:
        print(f'{report}: MISSING {missing}')
    else:
        macau_line = found.get('澳门亚盘', 'N/A')
        print(f'{report}: 澳门亚盘 OK - {macau_line[:80]}')
