import json

matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

if isinstance(data, dict) and 'groups' in data:
    for gn, gd in data['groups'].items():
        if isinstance(gd, dict) and 'matches' in gd:
            for m in gd['matches']:
                num = m.get('matchnum', '')
                if '7' in num or '8' in num or '9' in num:
                    print(f"num='{num}' home='{m.get('home','')}' away='{m.get('away','')}' league='{m.get('league','')}' fid='{m.get('fid','')}' home_id='{m.get('home_id','')}' away_id='{m.get('away_id','')}' macau='{m.get('macau_line','')}'")
