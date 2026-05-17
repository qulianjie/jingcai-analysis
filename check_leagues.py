# -*- coding: utf-8 -*-
import os, json

data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
leagues = {}

for x in sorted(os.listdir(data_dir)):
    if not os.path.isdir(os.path.join(data_dir, x)):
        continue
    meta_path = os.path.join(data_dir, x, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        league = meta.get('league', '')
        matchnum = meta.get('matchnum', '')
        if league:
            if league not in leagues:
                leagues[league] = []
            leagues[league].append(matchnum)

for league, matches in sorted(leagues.items()):
    print(f'{league}: {len(matches)} matches - {matches}')
