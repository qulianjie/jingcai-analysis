# -*- coding: utf-8 -*-
"""分析历史平局比赛的共同特征"""
import json, os

fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

dates = fb.get('dates', {})

# 检查4月6日、7日、21日
target_dates = ['2026-04-06', '2026-04-07', '2026-04-21']

all_draws = []

for date in target_dates:
    if date not in dates:
        print(f'{date}: 无数据')
        continue
    
    items = dates[date].get('feedback', [])
    print(f'\n=== {date} ({len(items)}场) ===')
    
    for item in items:
        score = item.get('score', '')
        predicted = item.get('predicted', '')
        actual = item.get('actual', '')
        correct = item.get('correct', False)
        combos = item.get('combos', {})
        s26 = item.get('s26', {})
        
        # 检查是否是平局
        is_draw = False
        if ':' in score:
            parts = score.split(':')
            try:
                if int(parts[0]) == int(parts[1]):
                    is_draw = True
            except:
                pass
        
        if is_draw:
            all_draws.append({
                'date': date,
                'match_num': item.get('match_num', '?'),
                'score': score,
                'predicted': predicted,
                'actual': actual,
                'correct': correct,
                'combos': combos,
                's26': s26,
            })
            
            print(f'  {item.get("match_num", "?")} | 比分:{score} | 预测:{predicted} | 正确:{correct}')
            # 显示关键combo
            key_fields = ['澳门亚盘', '竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路', 
                         '澳门同赔', '让球盘路_基准']
            for kf in key_fields:
                if kf in combos:
                    print(f'    {kf}: {combos[kf]}')
            
            # 显示s26数据
            if s26:
                for k in ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', '投注占比_主', '投注占比_平', '投注占比_客']:
                    if k in s26:
                        print(f'    {k}: {s26[k]}')

print(f'\n\n=== 平局共同特征统计 ===')
print(f'共找到 {len(all_draws)} 场平局\n')

# 统计各维度出现频率
from collections import Counter

dim_counters = {}
key_fields = ['澳门亚盘', '竞彩欧赔盘路', 'IW欧赔盘路', '百家欧赔盘路', 
             '澳门同赔', '让球盘路_基准']

for draw in all_draws:
    combos = draw.get('combos', {})
    for kf in key_fields:
        if kf not in dim_counters:
            dim_counters[kf] = Counter()
        val = combos.get(kf, '')
        if val:
            dim_counters[kf][val] += 1

for kf, counter in dim_counters.items():
    print(f'--- {kf} ---')
    for val, count in counter.most_common(5):
        pct = count / len(all_draws) * 100
        print(f'  {val}: {count}场 ({pct:.0f}%)')
    print()

# 统计s26数据
s26_counters = {}
s26_fields = ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏']

for draw in all_draws:
    s26 = draw.get('s26', {})
    for kf in s26_fields:
        if kf not in s26_counters:
            s26_counters[kf] = Counter()
        val = s26.get(kf, '')
        if val:
            s26_counters[kf][val] += 1

for kf, counter in s26_counters.items():
    print(f'--- {kf} ---')
    for val, count in counter.most_common(3):
        pct = count / len(all_draws) * 100
        print(f'  {val}: {count}场 ({pct:.0f}%)')
    print()

# 找出最常见的组合
print('\n=== 最常见组合模式 ===')
if all_draws:
    # 2D组合
    combo_2d = Counter()
    for draw in all_draws:
        combos = draw.get('combos', {})
        for i in range(len(key_fields)):
            for j in range(i+1, len(key_fields)):
                v1 = combos.get(key_fields[i], '')
                v2 = combos.get(key_fields[j], '')
                if v1 and v2:
                    combo_2d[f'{key_fields[i]}:{v1} × {key_fields[j]}:{v2}'] += 1
    
    print('最常见2D组合:')
    for combo, count in combo_2d.most_common(10):
        pct = count / len(all_draws) * 100
        print(f'  {combo}: {count}场 ({pct:.0f}%)')
