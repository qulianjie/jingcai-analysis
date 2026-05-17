# -*- coding: utf-8 -*-
"""Extract combo accuracy from feedback.json"""
import json, os

feedback_file = os.path.join(os.path.dirname(__file__), 'learnings', 'feedback.json')
with open(feedback_file, 'r', encoding='utf-8') as f:
    feedback = json.loads(f.read())

combo_stats = {}
for date, date_data in feedback.get('dates', {}).items():
    for match in date_data.get('feedback', []):
        for combo_key, combo_data in match.get('combos', {}).items():
            if combo_key not in combo_stats:
                combo_stats[combo_key] = {'total': 0, 'correct': 0}
            combo_stats[combo_key]['total'] += combo_data.get('total', 0)
            combo_stats[combo_key]['correct'] += combo_data.get('correct', 0)

print('=== Combo 准确率 (>=3场) ===')
for combo, stats in sorted(combo_stats.items(), key=lambda x: x[1]['correct']/max(x[1]['total'],1), reverse=True):
    if stats['total'] >= 3:
        acc = stats['correct'] / stats['total'] * 100
        print(f'{combo:<60} {stats["correct"]}/{stats["total"]} ({acc:.0f}%)')
