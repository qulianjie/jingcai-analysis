import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'Type: {type(data)}')
if isinstance(data, dict):
    items = data.values()
elif isinstance(data, list):
    items = data
else:
    print('Unknown format')
    exit()

total = len(list(items))
print(f'Total matches: {total}')

# Check structure
if data:
    first = list(data.values())[0] if isinstance(data, dict) else data[0]
    print(f'Keys: {list(first.keys())[:10]}')
    
    has_score = sum(1 for m in data.values() if isinstance(m, dict) and m.get('score'))
    print(f'Has score: {has_score}')
    print(f'No score: {total - has_score}')
