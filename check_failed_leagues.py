# -*- coding: utf-8 -*-
import os, json

dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', 
         '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']

S19_THRESHOLD = 1738
failed_leagues = {}

for date in dates:
    data_dir = 'jingcai/tasks/%s/data' % date
    if not os.path.isdir(data_dir):
        continue
    matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
    for m in matches:
        base = os.path.join(data_dir, m)
        step19 = os.path.join(base, 'group06_baijia', 'step19_baijia_compare.txt')
        if os.path.exists(step19):
            size = os.path.getsize(step19)
            if size <= S19_THRESHOLD:
                meta_path = os.path.join(base, 'meta.json')
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    league = meta.get('league', '')
                    if league not in failed_leagues:
                        failed_leagues[league] = 0
                    failed_leagues[league] += 1

results = ['失败match的联赛分布:']
for league, count in sorted(failed_leagues.items(), key=lambda x: -x[1]):
    results.append('  %s: %d场' % (league, count))

with open('jingcai/failed_leagues.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
