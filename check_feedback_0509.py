import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

dates = d.get('dates', {})
print('05-09 in feedback:', '2026-05-09' in dates)
print('All dates:', sorted(dates.keys()))

if '2026-05-09' in dates:
    matches = dates['2026-05-09']
    print(f'05-09 total matches: {len(matches)}')
    correct = [m for m in matches if m.get('correct')]
    print(f'Correct: {len(correct)}')
else:
    print('No feedback data for 2026-05-09')
