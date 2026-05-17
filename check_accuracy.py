# -*- coding: utf-8 -*-
import json, sys
from collections import defaultdict

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = data.get('_raw_combo_stats', {})

# Check what fields exist
sample_keys = list(stats.keys())[:50]
print('Sample combo labels:')
for k in sample_keys:
    v = stats[k]
    acc = v.get('accuracy', 0)
    total = v.get('total', 0)
    correct = v.get('correct', 0)
    print('  %s: acc=%.0f%% total=%d correct=%d' % (k, acc*100, total, correct))

# Find all combos with accuracy >= 60%, total >= 3
print('\nCombos with accuracy>=60%%, total>=3:')
high = []
for k, v in sorted(stats.items()):
    acc = v.get('accuracy', 0)
    total = v.get('total', 0)
    correct = v.get('correct', 0)
    if acc >= 0.60 and total >= 3:
        high.append((k, acc, total, correct))

print('Found %d combos' % len(high))
for k, acc, total, correct in sorted(high, key=lambda x: -x[1])[:20]:
    print('  %s: %.0f%% (%d/%d)' % (k, acc*100, correct, total))

# Find combos with accuracy <= 35%, total >= 3
print('\nCombos with accuracy<=35%%, total>=3:')
low = []
for k, v in sorted(stats.items()):
    acc = v.get('accuracy', 0)
    total = v.get('total', 0)
    correct = v.get('correct', 0)
    if acc <= 0.35 and total >= 3:
        low.append((k, acc, total, correct))

print('Found %d combos' % len(low))
for k, acc, total, correct in sorted(low, key=lambda x: x[1])[:15]:
    print('  %s: %.0f%% (%d/%d)' % (k, acc*100, correct, total))
