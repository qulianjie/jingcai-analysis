# -*- coding: utf-8 -*-
"""全量平局模式扫描器"""
import json, os
from collections import Counter

fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

dates = fb.get('dates', {})

# 收集所有平局
all_draws = []
all_matches = []

for date, date_info in dates.items():
    items = date_info.get('feedback', [])
    for item in items:
        score = item.get('score', '')
        is_draw = False
        if ':' in score:
            parts = score.split(':')
            try:
                if int(parts[0]) == int(parts[1]):
                    is_draw = True
            except:
                pass
        
        all_matches.append({
            'date': date,
            'is_draw': is_draw,
            'combos': item.get('combos', {}),
            's26': item.get('s26', {}),
            'predicted': item.get('predicted', ''),
        })
        
        if is_draw:
            all_draws.append({
                'date': date,
                'match_num': item.get('match_num', '?'),
                'score': score,
                'league': item.get('league', '?'),
                'combos': item.get('combos', {}),
                's26': item.get('s26', {}),
                'predicted': item.get('predicted', ''),
            })

print(f'总比赛数: {len(all_matches)}')
print(f'平局数: {len(all_draws)} ({len(all_draws)/len(all_matches)*100:.1f}%)')
print()

# 维度列表
key_fields = ['澳门亚盘', '竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路', 
             '澳门同赔', '让球盘路_基准', '欧赔趋势_dir', '亚盘趋势_dir', '百家对比_dir']

# 统计各维度在平局中的分布
print('=== 平局维度分布 ===')
for kf in key_fields:
    counter = Counter()
    for draw in all_draws:
        val = draw['combos'].get(kf, '')
        if val:
            counter[val] += 1
    
    if counter:
        print(f'\n--- {kf} ---')
        for val, count in counter.most_common(5):
            pct = count / len(all_draws) * 100
            print(f'  {val}: {count}场 ({pct:.0f}%)')

# 统计s26数据
s26_fields = ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', '庄家最看好']
print('\n=== 庄家盈亏分布 ===')
for kf in s26_fields:
    counter = Counter()
    for draw in all_draws:
        val = draw['s26'].get(kf, '')
        if val:
            counter[val] += 1
    
    if counter:
        print(f'\n--- {kf} ---')
        for val, count in counter.most_common(3):
            pct = count / len(all_draws) * 100
            print(f'  {val}: {count}场 ({pct:.0f}%)')

# 找2D组合模式
print('\n=== 平局高频2D组合 ===')
combo_2d = Counter()
for draw in all_draws:
    combos = draw['combos']
    for i in range(len(key_fields)):
        for j in range(i+1, len(key_fields)):
            v1 = combos.get(key_fields[i], '')
            v2 = combos.get(key_fields[j], '')
            if v1 and v2:
                combo_2d[f'{key_fields[i]}:{v1} × {key_fields[j]}:{v2}'] += 1

# 只显示出现>=3次的组合
top_2d = [(k, v) for k, v in combo_2d.most_common(20) if v >= 3]
for combo, count in top_2d:
    pct = count / len(all_draws) * 100
    print(f'  {combo}: {count}场 ({pct:.0f}%)')

# 找3D组合模式（>=3场）
print('\n=== 平局高频3D组合 ===')
combo_3d = Counter()
for draw in all_draws:
    combos = draw['combos']
    for i in range(len(key_fields)):
        for j in range(i+1, len(key_fields)):
            for k in range(j+1, len(key_fields)):
                v1 = combos.get(key_fields[i], '')
                v2 = combos.get(key_fields[j], '')
                v3 = combos.get(key_fields[k], '')
                if v1 and v2 and v3:
                    combo_3d[f'{key_fields[i]}:{v1} × {key_fields[j]}:{v2} × {key_fields[k]}:{v3}'] += 1

top_3d = [(k, v) for k, v in combo_3d.most_common(20) if v >= 3]
for combo, count in top_3d:
    pct = count / len(all_draws) * 100
    print(f'  {combo}: {count}场 ({pct:.0f}%)')

# 对比：非平局的维度分布（找差异）
print('\n=== 非平局维度分布（对比）===')
non_draws = [m for m in all_matches if not m['is_draw']]
print(f'非平局数: {len(non_draws)}')

for kf in ['竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路']:
    counter_draw = Counter()
    counter_non = Counter()
    
    for draw in all_draws:
        val = draw['combos'].get(kf, '')
        if val:
            counter_draw[val] += 1
    
    for m in non_draws:
        val = m['combos'].get(kf, '')
        if val:
            counter_non[val] += 1
    
    print(f'\n--- {kf} ---')
    print('  平局:')
    for val, count in counter_draw.most_common(3):
        pct = count / len(all_draws) * 100
        print(f'    {val}: {count}场 ({pct:.0f}%)')
    print('  非平局:')
    for val, count in counter_non.most_common(3):
        pct = count / len(non_draws) * 100
        print(f'    {val}: {count}场 ({pct:.0f}%)')
