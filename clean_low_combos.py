# -*- coding: utf-8 -*-
"""清理低准确率组合库中的低质量数据"""
import json

path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json'
d = json.load(open(path, encoding='utf-8'))

lc = d.get('low_accuracy_combos', [])
hc = d.get('high_accuracy_combos', [])

print('Before cleanup:')
print(f'  high_accuracy_combos: {len(hc)} items')
print(f'  low_accuracy_combos: {len(lc)} items')

# 清理低准确率组合：只保留 n>=10 的
cleaned_lc = [c for c in lc if c.get('total', c.get('n', 0)) >= 10]
print(f'\nAfter cleanup (n>=10):')
print(f'  low_accuracy_combos: {len(cleaned_lc)} items (removed {len(lc) - len(cleaned_lc)})')

d['low_accuracy_combos'] = cleaned_lc

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'\nCleaned low_accuracy_combos:')
for c in cleaned_lc[:15]:
    acc = c.get('accuracy', 0)
    n = c.get('total', c.get('n', 0))
    tag = c.get('tag', '')
    print(f'  acc={acc*100:.0f}% n={n} {tag}')
