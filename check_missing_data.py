# -*- coding: utf-8 -*-
"""检查缺失数据的比赛"""
import json, os

fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

dates = fb.get('dates', {})

# 找出没有combos的比赛
missing_combos = []
has_combos = []

for date, date_info in dates.items():
    items = date_info.get('feedback', [])
    for item in items:
        combos = item.get('combos', {})
        if not combos:
            missing_combos.append({
                'date': date,
                'match_num': item.get('match_num', '?'),
                'has_report': item.get('has_report', False),
            })
        else:
            has_combos.append(item)

print(f'总比赛数: {len(missing_combos) + len(has_combos)}')
print(f'有combos: {len(has_combos)}')
print(f'缺少combos: {len(missing_combos)}')

# 检查缺少combos的比赛是否有报告
no_report = [m for m in missing_combos if not m.get('has_report')]
print(f'\n缺少combos且无报告: {len(no_report)}')

if missing_combos:
    print(f'\n缺少combos的样例（前5场）:')
    for m in missing_combos[:5]:
        print(f'  {m["date"]} {m["match_num"]} has_report={m.get("has_report", False)}')

# 检查有combos的比赛的维度覆盖
print(f'\n=== 有combos比赛的维度覆盖 ===')
dim_fields = ['欧赔趋势_dir', '让球趋势_dir', '亚盘趋势_dir', '百家对比_dir', 
              '澳门亚盘', '竞彩欧赔盘路', 'IW欧赔盘路']

for df in dim_fields:
    count = 0
    for item in has_combos:
        if df in item.get('combos', {}):
            count += 1
    pct = count / len(has_combos) * 100
    print(f'  {df}: {count}场 ({pct:.0f}%)')
