# -*- coding: utf-8 -*-
import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('生成时间:', data.get('generated_at', '-'))
print('总场次:', data.get('total_matches', '-'))
print('总日期数:', data.get('total_dates', '-'))
print()

stats = data.get('_raw_combo_stats', {})
print('组合标签总数:', len(stats))
print()

# 统计各维度分布
dims = {}
for key in stats:
    parts = key.split(':')
    if len(parts) == 2:
        dim = parts[0]
        dims[dim] = dims.get(dim, 0) + 1

print('各维度标签数:')
for d in sorted(dims.items(), key=lambda x: -x[1]):
    print(f'  {d[0]}: {d[1]}个')

print()
high = data.get('high_accuracy_patterns', [])
print(f'高准确率组合(>=60%,>=5场): {len(high)}个')
for p in high[:10]:
    combo = p.get('combo', '')
    acc = p.get('accuracy', 0)
    correct = p.get('correct', 0)
    total = p.get('total', 0)
    print(f'  {combo}: {acc:.0%} ({correct}/{total})')

print()
low = data.get('low_accuracy_patterns', [])
print(f'低准确率组合(<=35%,>=5场): {len(low)}个')
for p in low[:5]:
    combo = p.get('combo', '')
    acc = p.get('accuracy', 0)
    correct = p.get('correct', 0)
    total = p.get('total', 0)
    print(f'  {combo}: {acc:.0%} ({correct}/{total})')
