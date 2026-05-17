import os, json
base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
targets = ['match7', 'match8', 'match9', 'match14', 'match16', 'match17', 'match19', 'match20']
for t in targets:
    p = os.path.join(base, t, 'meta.json')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            j = json.load(f)
        print(f"{t}: league='{j.get('league','')}' home='{j.get('home','')}' away='{j.get('away','')}' home_id='{j.get('home_id','')}' away_id='{j.get('away_id','')}' fid='{j.get('fid','')}' macau='{j.get('macau_line','')}'")
    else:
        print(f"{t}: no meta.json")
