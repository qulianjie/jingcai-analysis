# -*- coding: utf-8 -*-
"""完整检查反馈学习机制状态"""
import json, os, re

print('=' * 60)
print('竞彩反馈学习机制 - 完整状态检查')
print('=' * 60)

# 1. 检查feedback.json
fb_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
with open(fb_path, 'r', encoding='utf-8') as f:
    fb = json.load(f)

dates = fb.get('dates', {})
total_matches = sum(len(d.get('feedback', [])) for d in dates.values())
matches_with_combos = 0
matches_with_s26 = 0
matches_with_dims = 0

for date, date_info in dates.items():
    for item in date_info.get('feedback', []):
        combos = item.get('combos', {})
        s26 = item.get('s26', {})
        
        if combos:
            matches_with_combos += 1
        if s26:
            matches_with_s26 += 1
        
        # 检查有维度标签
        dim_fields = ['欧赔趋势_dir', '亚盘趋势_dir', '百家对比_dir', '庄家盈亏_dir']
        for df in dim_fields:
            if df in combos:
                matches_with_dims += 1
                break

print(f'\n[1] feedback.json 数据')
print(f'    总比赛数: {total_matches}')
print(f'    有combos: {matches_with_combos} ({matches_with_combos/total_matches*100:.0f}%)')
print(f'    有s26: {matches_with_s26} ({matches_with_s26/total_matches*100:.0f}%)')
print(f'    有维度标签: {matches_with_dims} ({matches_with_dims/total_matches*100:.0f}%)')

# 2. 检查learned_patterns_v2.json
lp_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json'
if os.path.exists(lp_path):
    lp = json.load(open(lp_path, 'r', encoding='utf-8'))
    raw_combos = lp.get('_raw_combo_stats', {})
    
    print(f'\n[2] learned_patterns_v2.json')
    print(f'    更新时间: {lp.get("updated", "?")}')
    print(f'    总组合数: {len(raw_combos)}')
    
    # 分类统计
    categories = {
        '欧赔趋势': 0,
        '亚盘趋势': 0,
        '让球趋势': 0,
        '百家对比': 0,
        '庄家盈亏': 0,
        '澳门亚盘': 0,
        '竞彩盘路': 0,
        'IW盘路': 0,
        '百家盘路': 0,
        '澳门同赔': 0,
        '投注占比': 0,
        '其他': 0,
    }
    
    for k in raw_combos:
        matched = False
        for cat in categories:
            if k.startswith(cat + ':'):
                categories[cat] += 1
                matched = True
                break
        if not matched:
            categories['其他'] += 1
    
    print(f'\n    维度分布:')
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f'      {cat}: {count}')
    
    # 检查高准确率组合
    high_acc = lp.get('high_accuracy_combos', [])
    print(f'\n[3] 高准确率组合 (>=60%, >=5场): {len(high_acc)}个')
    for combo in high_acc[:5]:
        print(f'    {combo.get("combo", "?")}: {combo.get("accuracy", 0):.0%} ({combo.get("correct", 0)}/{combo.get("total", 0)})')

# 3. 检查match_num格式
print(f'\n[4] match_num格式检查')
sample_dates = ['2026-05-03', '2026-04-06', '2026-04-21']
for date in sample_dates:
    if date in dates:
        items = dates[date].get('feedback', [])
        if items:
            mn = items[0].get('match_num', '?')
            print(f'    {date}: match_num = "{mn}" (格式: {"✅ 标准" if mn.isdigit() else "⚠️ 非标准"})')

# 4. 检查step26数据
print(f'\n[5] step26数据完整性')
s26_fields = ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏', '投注占比_主', '投注占比_平', '投注占比_客']
for field in s26_fields:
    count = 0
    for date, date_info in dates.items():
        for item in date_info.get('feedback', []):
            if field in item.get('s26', {}):
                count += 1
    pct = count / total_matches * 100
    print(f'    {field}: {count}场 ({pct:.0f}%)')

print(f'\n' + '=' * 60)
print('结论:')
if matches_with_combos >= 200 and len(raw_combos) >= 500:
    print('  ✅ 反馈学习机制已基本修复完成')
    print(f'  ✅ {matches_with_combos}场比赛有完整组合数据')
    print(f'  ✅ {len(raw_combos)}个组合模式已学习')
else:
    print(f'  ⚠️ 仍有问题需要修复')
print('=' * 60)
