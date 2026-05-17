import json, os

failed = [
    ('2026-05-08', 'match11'),
    ('2026-05-09', 'match5'),
    ('2026-05-09', 'match7'),
    ('2026-05-10', 'match1'),
    ('2026-05-11', 'match6'),
    ('2026-05-12', 'match7'),
    ('2026-05-12', 'match17')
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
        line = '%s/%s: %s vs %s | %s | 竞彩编号:%s | fid:%s' % (date, name, home, away, league, match_num, fid)
        results.append(line)
        
        # 找最终报告
        report_dir = os.path.dirname(os.path.dirname(path))
        for f in os.listdir(report_dir):
            if f.endswith('.md'):
                results.append('  报告: %s' % f)
                break
    else:
        results.append('%s/%s: 不存在' % (date, name))

with open('jingcai/failed_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/failed_results.txt')
