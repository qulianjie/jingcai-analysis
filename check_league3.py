# -*- coding: utf-8 -*-
import json, re

with open('C:/Users/lianjie/.openclaw/workspace/jingcai/leagues_all.json', 'r', encoding='utf-8') as f:
    leagues = json.load(f)

# Extract just the Chinese prefix from each name
# e.g. "英Premier League" -> "英超" or "英"
# We'll build: league_name -> id where league_name is the Chinese part + maybe one more char

print('League name analysis:')
for item in leagues[:10]:
    name = item['name']
    # The pattern: Chinese chars + English
    # e.g. "英超Premier League" or "西La Liga"
    # We want to extract the full Chinese part
    m = re.match(r'^([\u4e00-\u9fff]+)', name)
    cn = m.group(1) if m else ''
    eng = name[len(cn):].split()[0] if len(cn) < len(name) else ''
    print(f'  id={item["id"]} full="{name}" cn="{cn}" eng="{eng}"')

# Also check league_map.json to see what keys it has
with open('C:/Users/lianjie/.openclaw/workspace/jingcai/league_map.json', 'r', encoding='utf-8') as f:
    lmap = json.load(f)

print(f'\nleague_map.json has {len(lmap)} keys')
print('Sample keys:')
for k in list(lmap.keys())[:10]:
    print(f'  "{k}" -> {lmap[k][:3]}')
