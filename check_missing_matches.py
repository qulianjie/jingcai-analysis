import json

matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get all matches
all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

print('Total matches:', len(all_matches))
print()

# Missing: 007, 008, 009, 021, 022, 023, 026, 029, 030
missing_nums = ['007', '008', '009', '021', '022', '023', '026', '029', '030']

for m in all_matches:
    num = m.get('matchnum', '')
    if num in missing_nums:
        print(f"{num}: {m.get('home','')} vs {m.get('away','')} | league={m.get('league','')} | fid={m.get('fid','')} | home_id={m.get('home_id','')} | away_id={m.get('away_id','')} | macau={m.get('macau_line','')}")
