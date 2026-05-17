# -*- coding: utf-8 -*-
"""检查反馈学习机制修复状态"""
import json, os

fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

dates = fb.get('dates', {})

# 检查几个日期
check_dates = ['2026-05-03', '2026-05-04', '2026-04-06']

print('=== 反馈数据检查 ===\n')

for date in check_dates:
    if date not in dates:
        print(f'{date}: 无数据')
        continue
    
    items = dates[date].get('feedback', [])
    print(f'{date}: {len(items)}场')
    
    if items:
        item = items[0]
        mn = item.get('match_num', '?')
        combos = item.get('combos', {})
        s26 = item.get('s26', {})
        
        print(f'  match_num: {mn}')
        print(f'  combos字段数: {len(combos)}')
        print(f'  combos样例: {list(combos.keys())[:5]}')
        print(f'  s26字段数: {len(s26)}')
        print(f'  s26样例: {list(s26.keys())[:5]}')
        
        # 检查单维标签
        dim_fields = ['欧赔趋势_dir', '让球趋势_dir', '亚盘趋势_dir', '百家对比_dir']
        has_dim = False
        for df in dim_fields:
            if df in combos:
                has_dim = True
                print(f'  {df}: {combos[df]}')
                break
        
        if not has_dim:
            print('  ⚠️ 单维标签为空')
        
        # 检查庄家盈亏
        if '庄家胜盈亏' in s26:
            print(f'  庄家胜盈亏: {s26["庄家胜盈亏"]}')
            print(f'  庄家平盈亏: {s26.get("庄家平盈亏", "?")}')
            print(f'  庄家负盈亏: {s26.get("庄家负盈亏", "?")}')
        
        print()

# 统计总数据
total_matches = 0
total_with_combos = 0
total_with_s26 = 0
total_with_dims = 0

for date, date_info in dates.items():
    items = date_info.get('feedback', [])
    total_matches += len(items)
    
    for item in items:
        combos = item.get('combos', {})
        s26 = item.get('s26', {})
        
        if combos:
            total_with_combos += 1
        if s26:
            total_with_s26 += 1
        
        # 检查是否有单维标签
        for df in ['欧赔趋势_dir', '让球趋势_dir', '亚盘趋势_dir', '百家对比_dir']:
            if df in combos:
                total_with_dims += 1
                break

print(f'\n=== 总统计 ===')
print(f'总比赛数: {total_matches}')
print(f'有combos: {total_with_combos} ({total_with_combos/total_matches*100:.0f}%)')
print(f'有s26: {total_with_s26} ({total_with_s26/total_matches*100:.0f}%)')
print(f'有单维标签: {total_with_dims} ({total_with_dims/total_matches*100:.0f}%)')

# 检查 learned_patterns_v2.json
lp_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json'
if os.path.exists(lp_path):
    lp = json.load(open(lp_path, 'r', encoding='utf-8'))
    raw_combos = lp.get('_raw_combo_stats', {})
    print(f'\n=== learned_patterns_v2.json ===')
    print(f'组合标签数: {len(raw_combos)}')
    
    # 检查是否有精细维度
    fine_dims = ['澳门亚盘', '竞彩盘路', 'IW盘路', '庄家胜盈亏']
    fine_count = 0
    for k in raw_combos:
        for fd in fine_dims:
            if k.startswith(fd + ':'):
                fine_count += 1
                break
    
    print(f'精细维度组合数: {fine_count}')
    print(f'更新时间: {lp.get("updated", "?")}')
