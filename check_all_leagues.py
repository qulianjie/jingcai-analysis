import json, os

dates = ['2026-05-07','2026-05-08','2026-05-09','2026-05-10','2026-05-11','2026-05-12','2026-05-13']
for date in dates:
    data_dir = os.path.join(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks', date, 'data')
    if not os.path.exists(data_dir):
        continue
    empty_leagues = []
    for fn in sorted(os.listdir(data_dir)):
        if not fn.startswith('match'):
            continue
        mp = os.path.join(data_dir, fn, 'meta.json')
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding='utf-8'))
            league = meta.get('league', '')
            fid = meta.get('fid', '')
            if not league:
                empty_leagues.append((fn, fid))
    if empty_leagues:
        print(f'{date}: {len(empty_leagues)} empty leagues')
        for name, fid in empty_leagues:
            print(f'  {name} (fid={fid})')
    else:
        print(f'{date}: all leagues populated')
