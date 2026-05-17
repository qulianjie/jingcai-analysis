# -*- coding: utf-8 -*-
import os, json

path = 'jingcai/league_map.json'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('league_map.json exists, %d entries' % len(data))
    for k, v in sorted(data.items())[:10]:
        print('  "%s": %s' % (k, v))
else:
    print('league_map.json does not exist')
