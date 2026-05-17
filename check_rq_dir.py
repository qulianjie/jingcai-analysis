# -*- coding: utf-8 -*-
"""检查让球趋势_dir为什么是空的"""
import json, os, re

# 找一个有报告的比赛
tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
date_dir = os.path.join(tasks_dir, '2026-05-03')

# 找周日001的报告
for fname in os.listdir(date_dir):
    if '001' in fname and fname.endswith('.md'):
        fpath = os.path.join(date_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f'=== {fname} ===')
        
        # 检查各维度信号
        dim_pattern = r'\|\s*(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|庄家盈亏)\s*\|\s*([+-]?\d+\.\d+)\s+(利好主|利好客|中立)\s*\|\s*(\d+)%'
        
        print('\n各维度信号:')
        for m in re.finditer(dim_pattern, content):
            print(f'  {m.group(1)}: {m.group(2)} {m.group(3)} ({m.group(4)}%)')
        
        # 检查让球相关
        print('\n让球相关:')
        rq_lines = [line for line in content.split('\n') if '让球' in line and ('利好' in line or '趋势' in line)]
        for line in rq_lines[:5]:
            print(f'  {line.strip()}')
        
        # 检查报告头部
        print('\n报告头部:')
        for line in content.split('\n')[:15]:
            if '让球' in line or '亚盘' in line:
                print(f'  {line.strip()}')
        
        break
