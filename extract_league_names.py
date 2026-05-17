# -*- coding: utf-8 -*-
"""从所有meta.json中提取实际出现过的竞彩联赛简称"""
import json, os, glob

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
leagues = {}
count = 0

for meta_path in glob.glob(os.path.join(tasks_dir, '**', 'meta.json'), recursive=True):
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        league = meta.get('league', '')
        if league:
            leagues[league] = leagues.get(league, 0) + 1
            count += 1
    except:
        continue

print(f'总比赛数: {count}')
print(f'不同联赛数: {len(leagues)}')
print()

# 按出现次数排序
sorted_leagues = sorted(leagues.items(), key=lambda x: -x[1])
for name, cnt in sorted_leagues:
    print(f'  {cnt:4d}  {name}')

# 输出到文件
out_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\jingcai_league_names.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    for name, cnt in sorted_leagues:
        f.write(f'{name}\n')
print(f'\n已保存到: {out_path}')
