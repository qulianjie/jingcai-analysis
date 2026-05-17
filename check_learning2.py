# -*- coding: utf-8 -*-
import json

d = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', encoding='utf-8'))

print('version:', d.get('version'))
print('updated:', d.get('updated'))
print('total_matches:', d.get('total_matches'))
print('total_dates:', d.get('total_dates'))

# Check feedback.json size
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))
print('\nfeedback.json keys:', len(fb))
dates = sorted(fb.keys())
print('date range:', dates[0], '~', dates[-1])
print('total dates with feedback:', len(dates))

# Count total feedback entries
total_fb = 0
for date, matches in fb.items():
    total_fb += len(matches)
print('total feedback entries:', total_fb)

# Check how many have result
with_result = 0
for date, matches in fb.items():
    for m in matches:
        if m.get('result') and m['result'] != '待查':
            with_result += 1
print('entries with result:', with_result)

# Check panlu_accuracy
pa = d.get('panlu_accuracy', [])
print('\npanlu_accuracy:', len(pa), '条')

# Check confidence_accuracy
ca = d.get('confidence_accuracy', {})
print('confidence_accuracy:', len(ca), 'keys')
for k, v in list(ca.items())[:5]:
    print('  %s: %s' % (k, json.dumps(v, ensure_ascii=False)))

# Check _raw_combo_stats
raw = d.get('_raw_combo_stats', {})
print('\n_raw_combo_stats:', len(raw), 'entries')
# Show a few
for k, v in list(raw.items())[:3]:
    print('  %s: %s' % (k, json.dumps(v, ensure_ascii=False)))
