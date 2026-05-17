import json
d = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\matches_data.json', 'r', encoding='utf-8'))
for k, v in d['groups'].items():
    print(f'{k}: {v["count"]}场')
    for m in v['matches']:
        print(f'  {m["matchnum"]} | {m["home"]} vs {m["away"]}')
