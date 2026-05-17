# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

d = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', encoding='utf-8'))

print('\n=== 高准确率组合 (TOP30) ===\n')
for c in d.get('high_accuracy_combos', [])[:30]:
    tag = c.get('tag', '')
    acc = c['accuracy']
    cor = c['correct']
    tot = c['total']
    print(f'  {tag}: {acc:.0%} ({cor}/{tot})')

print(f'\n=== 低准确率组合 (TOP20) ===\n')
for c in d.get('low_accuracy_combos', [])[:20]:
    tag = c.get('tag', '')
    acc = c['accuracy']
    cor = c['correct']
    tot = c['total']
    print(f'  {tag}: {acc:.0%} ({cor}/{tot})')

# 提取所有唯一标签
all_tags = set()
for c in d.get('high_accuracy_combos', []) + d.get('low_accuracy_combos', []):
    tag = c.get('tag', '')
    for part in tag.split('\u00d7'):
        all_tags.add(part.strip())

print(f'\n=== 所有唯一标签 ({len(all_tags)}个) ===\n')
for t in sorted(all_tags):
    print(f'  {t}')

# 按类别分组
print(f'\n=== 标签分类统计 ===\n')
categories = {}
for t in sorted(all_tags):
    if ':' in t:
        cat = t.split(':')[0]
    else:
        cat = '其他'
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(t)

for cat in sorted(categories.keys()):
    items = categories[cat]
    print(f'  {cat} ({len(items)}个):')
    for item in items[:10]:
        print(f'    {item}')
    if len(items) > 10:
        print(f'    ... 还有{len(items)-10}个')
