import json, re

matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

# Missing: 007, 008, 009, 021, 022, 023, 026, 029, 030
missing_nums = {'007', '008', '009', '021', '022', '023', '026', '029', '030'}

print('Total matches:', len(all_matches))
print()
for m in all_matches:
    num_raw = m.get('matchnum', '')
    m2 = re.search(r'(\d{3})$', num_raw)
    if m2:
        num = m2.group(1)
        if num in missing_nums:
            print(f"{num}: {m.get('home','')} vs {m.get('away','')} | league={m.get('league','')} | fid={m.get('fid','')}")
