# -*- coding: utf-8 -*-
import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Show all top-level keys
print('Top-level keys:')
for k in sorted(data.keys()):
    v = data[k]
    if isinstance(v, (int, float, str, bool, type(None))):
        print('  %s: %s' % (k, v))
    elif isinstance(v, list):
        print('  %s: list[%d]' % (k, len(v)))
    elif isinstance(v, dict):
        print('  %s: dict[%d keys]' % (k, len(v)))

# Check if there's a separate accuracy field
print()
print('Checking accuracy in _raw_combo_stats...')
stats = data.get('_raw_combo_stats', {})
sample = list(stats.items())[:3]
for k, v in sample:
    print('  %s: %s' % (k, v))

# Check high_accuracy_patterns
high = data.get('high_accuracy_patterns', [])
print()
print('high_accuracy_patterns: %d entries' % len(high))
for p in high[:5]:
    print('  %s' % p)

# Check if there's a league_accuracy section
league = data.get('league_accuracy', {})
print()
print('league_accuracy: %d entries' % len(league))
for k, v in sorted(league.items(), key=lambda x: -x[1].get('accuracy', 0))[:10]:
    print('  %s: %s' % (k, v))
