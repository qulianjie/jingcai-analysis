import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\matches_data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

groups = d.get('groups', {})
days = sorted(groups.keys())
print('Days:', days)

for g in days:
    print(f'{g}: {groups[g]["count"]} matches')

for g in days:
    for m in groups[g]['matches'][:15]:
        print(f'  {m["matchnum"]} {m["league"]} {m["home"]} vs {m["away"]} (fid={m.get("fid","")})')
