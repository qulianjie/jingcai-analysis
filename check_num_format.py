import json

matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

print('Total matches:', len(all_matches))
print()
# Show first 5 matchnums
for m in all_matches[:5]:
    num = m.get('matchnum', '')
    print(f"matchnum='{num}' repr={repr(num)}")
