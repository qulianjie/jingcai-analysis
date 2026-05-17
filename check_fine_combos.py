# -*- coding: utf-8 -*-
"""查看精细组合标签"""
import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

combos = data.get('_raw_combo_stats', {})

print(f'总组合数: {len(combos)}')
print()

# 分类显示
categories = {
    '澳门亚盘': [],
    '竞彩盘路': [],
    'IW盘路': [],
    '百家盘路': [],
    '澳门同赔': [],
    '投注占比精确': [],
    '庄家盈亏': [],
}

for k in combos:
    for cat in categories:
        if k.startswith(cat + ':'):
            categories[cat].append(k)
            break

for cat, tags in categories.items():
    print(f'=== {cat} ({len(tags)} 个) ===')
    for t in sorted(tags)[:10]:
        stats = combos[t]
        acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f'  {t}: {stats["correct"]}/{stats["total"]} = {acc:.1%}')
    if len(tags) > 10:
        print(f'  ... 还有 {len(tags)-10} 个')
    print()
