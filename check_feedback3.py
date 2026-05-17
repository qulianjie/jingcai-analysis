import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total dates: {len(data.get("dates", {}))}')

total_matches = 0
has_score = 0
no_score_dates = []

for date, date_data in data.get('dates', {}).items():
    matches = date_data.get('feedback', [])
    total_matches += len(matches)
    has_score += sum(1 for m in matches if m.get('score'))
    if not any(m.get('score') for m in matches):
        no_score_dates.append(date)

print(f'Total matches: {total_matches}')
print(f'Has score: {has_score}')
print(f'No score: {total_matches - has_score}')
print(f'Dates without any score: {len(no_score_dates)}')
if no_score_dates:
    print(f'First 5 no-score dates: {no_score_dates[:5]}')
