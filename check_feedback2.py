import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total dates: {len(data)}')

total_matches = 0
has_score = 0

for date, matches in data.items():
    if isinstance(matches, list):
        total_matches += len(matches)
        has_score += sum(1 for m in matches if isinstance(m, dict) and m.get('score'))

print(f'Total matches: {total_matches}')
print(f'Has score: {has_score}')
print(f'No score: {total_matches - has_score}')
