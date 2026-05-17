import json, os
d = r'jingcai\tasks\2026-05-05\data'
for m in sorted(os.listdir(d)):
    if not os.path.isdir(os.path.join(d, m)): continue
    p = os.path.join(d, m, 'meta.json')
    j = json.load(open(p, encoding='utf-8'))
    print(f"{m}: home_id={j.get('home_id','MISSING')} away_id={j.get('away_id','MISSING')} home={j.get('home','')} away={j.get('away','')}")
