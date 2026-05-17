# -*- coding: utf-8 -*-
"""检查让球趋势提取"""
import json, os, re

# 检查feedback.json中05-03第一场
fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

items = fb['dates']['2026-05-03']['feedback']
item = items[0]
combos = item.get('combos', {})

print('=== 所有让球相关keys ===')
for k in sorted(combos.keys()):
    if '让球' in k or 'rq' in k.lower():
        print(f'  {k}: {combos[k]}')

print('\n=== 所有keys ===')
for k in sorted(combos.keys()):
    print(f'  {k}: {combos[k]}')

# 检查报告
tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
date_dir = os.path.join(tasks_dir, '2026-05-03')

for fname in os.listdir(date_dir):
    if '001' in fname and fname.endswith('.md'):
        fpath = os.path.join(date_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查"各维度信号"部分
        if '各维度信号' in content:
            start = content.find('各维度信号')
            section = content[start:start+800]
            print('\n=== 各维度信号部分 ===')
            print(section)
        
        break
