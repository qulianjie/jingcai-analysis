# -*- coding: utf-8 -*-
import json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(SCRIPT_DIR, 'leagues_all.json')
map_path = os.path.join(SCRIPT_DIR, 'league_map.json')

with open(json_path, 'r', encoding='utf-8') as f:
    leagues = json.load(f)

# Find 德甲
print('Searching for 德甲 in leagues_all.json:')
for item in leagues:
    if '德甲' in item['name'] or 'Bundesliga' in item['name']:
        print(f'  id={item["id"]} name={repr(item["name"])}')

# Check league_map.json
with open(map_path, 'r', encoding='utf-8') as f:
    lmap = json.load(f)

print('\nleague_map.json entries for 德甲:')
for k, v in lmap.items():
    if '德甲' in k or 'Bundesliga' in k or '德' in k:
        print(f'  {repr(k)} -> {v}')

# Build the mapping the same way as step8_1923_extractor.py
direct = {}
for item in leagues:
    direct[item['name']] = item['id']

print('\nDirect map entries containing 德:')
for k, v in direct.items():
    if '德' in k or 'Bundesliga' in k:
        print(f'  {repr(k)} -> {v}')

# Try the mapping logic
jingcai_map = {}
try:
    from league_mapper import load_map as _load_map
    jingcai_map = _load_map()
except:
    pass

print('\nleague_mapper entries for 德甲:')
for k, v in jingcai_map.items():
    if '德甲' in k:
        print(f'  {repr(k)} -> {v}')

# Build league_map the same way
league_map = {}
for key, aliases in jingcai_map.items():
    for src_name in [key] + aliases:
        if src_name in direct:
            league_map[key] = direct[src_name]
            break
        for dname, did in direct.items():
            if src_name[:2] in dname or dname[:2] in src_name:
                league_map[key] = did
                break
        if key in league_map:
            break

print(f'\nFinal league_map[德甲] = {league_map.get("德甲", "NOT FOUND")}')
print(f'Total mappings: {len(league_map)}')
