# -*- coding: utf-8 -*-
import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

out = []
out.append('Updated: %s' % data.get('updated', '-'))
out.append('Total matches: %d, dates: %d' % (data.get('total_matches', 0), data.get('total_dates', 0)))
out.append('Combo label count: %d' % len(data.get('_raw_combo_stats', {})))
out.append('')

# Raw combo stats - calculate accuracy
stats = data.get('_raw_combo_stats', {})
out.append('=== Single-dimension accuracy (>=5 matches) ===')
items = []
for k, v in stats.items():
    total = v.get('total', 0)
    correct = v.get('correct', 0)
    if total >= 5:
        acc = correct / total if total > 0 else 0
        items.append((k, acc, total, correct))

# High accuracy
high_items = [x for x in items if x[1] >= 0.60]
high_items.sort(key=lambda x: -x[1])
out.append('High accuracy (>=60%%, >=5): %d' % len(high_items))
for k, acc, total, correct in high_items[:15]:
    out.append('  %s: %.0f%% (%d/%d)' % (k, acc*100, correct, total))

# Low accuracy
low_items = [x for x in items if x[1] <= 0.35]
low_items.sort(key=lambda x: x[1])
out.append('')
out.append('Low accuracy (<=35%%, >=5): %d' % len(low_items))
for k, acc, total, correct in low_items[:10]:
    out.append('  %s: %.0f%% (%d/%d)' % (k, acc*100, correct, total))

# High accuracy combos from the pre-computed list
out.append('')
high_combos = data.get('high_accuracy_combos', [])
out.append('Pre-computed high accuracy combos: %d' % len(high_combos))
for p in high_combos[:15]:
    if isinstance(p, dict):
        out.append('  %s' % json.dumps(p, ensure_ascii=False))
    else:
        out.append('  %s' % str(p))

# Low accuracy combos
low_combos = data.get('low_accuracy_combos', [])
out.append('')
out.append('Pre-computed low accuracy combos: %d' % len(low_combos))
for p in low_combos[:5]:
    if isinstance(p, dict):
        out.append('  %s' % json.dumps(p, ensure_ascii=False))
    else:
        out.append('  %s' % str(p))

# League accuracy
league = data.get('league_accuracy', [])
out.append('')
out.append('League accuracy: %d leagues' % len(league))
for p in league[:15]:
    if isinstance(p, dict):
        out.append('  %s' % json.dumps(p, ensure_ascii=False))

result = '\n'.join(out)
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\accuracy_out.txt', 'w', encoding='utf-8') as f:
    f.write(result)
print(result)
