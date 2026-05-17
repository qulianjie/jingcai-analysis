# -*- coding: utf-8 -*-
import json

d = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', encoding='utf-8'))

hc = d.get('high_accuracy_combos', [])
lc = d.get('low_accuracy_combos', [])
lr = d.get('league_accuracy', [])
ep = d.get('expert_patterns', [])

print('=== high_accuracy_combos: %d 条 ===' % len(hc))
for c in sorted(hc, key=lambda x: x.get('accuracy', 0), reverse=True)[:10]:
    acc = c.get('accuracy', 0)
    n = c.get('n', c.get('total', 0))
    tag = c.get('tag', '')
    print('  acc=%.0f%%  n=%d  %s' % (acc * 100, n, tag))

print('\n=== low_accuracy_combos: %d 条 ===' % len(lc))
for c in sorted(lc, key=lambda x: x.get('accuracy', 0))[:10]:
    acc = c.get('accuracy', 0)
    n = c.get('n', c.get('total', 0))
    tag = c.get('tag', '')
    print('  acc=%.0f%%  n=%d  %s' % (acc * 100, n, tag))

print('\n=== league_accuracy: %d 条 ===' % len(lr))
for l in sorted(lr, key=lambda x: x.get('accuracy', 0), reverse=True)[:15]:
    acc = l.get('accuracy', 0)
    total = l.get('total', 0)
    league = l.get('league', '')
    print('  acc=%.0f%%  total=%d  %s' % (acc * 100, total, league))

print('\n=== expert_patterns: %d 条 ===' % len(ep))
for e in sorted(ep, key=lambda x: x.get('accuracy', 0), reverse=True)[:5]:
    acc = e.get('accuracy', 0)
    sample = e.get('sample', e.get('n', 0))
    league = e.get('league', '')
    pattern = e.get('pattern', '')
    print('  acc=%.0f%%  sample=%d  %s: %s' % (acc * 100, sample, league, pattern))

print('\n=== Top-level keys ===')
for k in d.keys():
    if isinstance(d[k], list):
        print('  %s: %d items' % (k, len(d[k])))
    elif isinstance(d[k], dict):
        print('  %s: %d keys' % (k, len(d[k])))
    else:
        print('  %s: %s' % (k, type(d[k]).__name__))
