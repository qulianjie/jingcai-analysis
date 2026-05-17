import json, os

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-11\data'
for fn in sorted(os.listdir(d)):
    if fn.startswith('match'):
        mp = os.path.join(d, fn, 'meta.json')
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding='utf-8'))
            print(f'{fn}: league={meta.get("league", "<missing>")}')
