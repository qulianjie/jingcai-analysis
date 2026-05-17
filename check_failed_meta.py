import json, os

failed = [
    ('2026-05-08', 'match11_赫尔城__米尔沃尔'),
    ('2026-05-09', 'match7_米堡__南安普敦'),
    ('2026-05-11', 'match6_米尔沃尔__赫尔城'),
    ('2026-05-12', 'match7_南安普敦__米堡'),
    ('2026-05-12', 'match17_南安普敦__米堡'),
]

results = []
for date, name in failed:
    path = 'jingcai/tasks/%s/data/%s/meta.json' % (date, name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        home = meta.get('home', '?')
        away = meta.get('away', '?')
        league = meta.get('league', '?')
        match_num = meta.get('match_num', '?')
        fid = meta.get('fid', '?')
        results.append('%s/%s: %s vs %s | %s | 竞彩编号:%s | fid:%s' % (date, name, home, away, league, match_num, fid))
    else:
        results.append('%s/%s: 不存在' % (date, name))

with open('jingcai/failed_meta.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/failed_meta.txt')
