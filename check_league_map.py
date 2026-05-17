# -*- coding: utf-8 -*-
import json

with open('C:/Users/lianjie/.openclaw/workspace/jingcai/league_map.json', 'r', encoding='utf-8') as f:
    lmap = json.load(f)

# Check 德甲 and 日职 mappings
for key in ['德甲', '日职', '韩职', '澳超', '葡超', '英足总杯', '亚冠']:
    if key in lmap:
        print(f'{key} -> {lmap[key]}')
    else:
        print(f'{key} -> NOT FOUND in league_map.json')
        # Search for similar keys
        for k in lmap.keys():
            if key in k or k in key:
                print(f'  Similar: {k} -> {lmap[k]}')
