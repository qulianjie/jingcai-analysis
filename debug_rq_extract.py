# -*- coding: utf-8 -*-
"""调试让球趋势提取"""
import json, os, re

# 找一个有combos的比赛
fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

# 找05-03的第一场
items = fb['dates']['2026-05-03']['feedback']
item = items[0]
combos = item.get('combos', {})

print('=== combos keys ===')
for k in sorted(combos.keys()):
    if '让球' in k or 'rq' in k.lower():
        print(f'  {k}: {combos[k]}')

# 检查报告
tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
date_dir = os.path.join(tasks_dir, '2026-05-03')

for fname in os.listdir(date_dir):
    if '001' in fname and fname.endswith('.md'):
        fpath = os.path.join(date_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 手动运行提取逻辑
        dim_pattern = r'\|\s*(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|庄家盈亏)\s*\|\s*([+-]?\d+\.\d+)\s+(利好主|利好客|中立)\s*\|\s*(\d+)%'
        
        print('\n=== 正则匹配结果 ===')
        for m in re.finditer(dim_pattern, content):
            print(f'  {m.group(1)}: {m.group(2)} {m.group(3)} ({m.group(4)}%)')
        
        # 检查报告里有没有"各维度信号"部分
        if '各维度信号' in content:
            print('\n=== 报告中有"各维度信号"部分 ===')
            # 提取这部分
            start = content.find('各维度信号')
            end = content.find('---', start)
            section = content[start:end] if end > start else content[start:start+500]
            print(section[:300])
        else:
            print('\n⚠️ 报告中没有"各维度信号"部分')
        
        break
