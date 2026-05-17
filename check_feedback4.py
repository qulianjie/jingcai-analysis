import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8') as f:
    data = json.load(f)

# Check a sample match
for date, date_data in list(data.get('dates', {}).items())[:2]:
    matches = date_data.get('feedback', [])
    print(f'Date: {date}, matches: {len(matches)}')
    if matches:
        m = matches[0]
        print(f'  First match keys: {list(m.keys())}')
        print(f'  Score: {m.get("score")}')
        print(f'  Correct: {m.get("correct")}')
        print(f'  Combos: {m.get("combos", {})}')
