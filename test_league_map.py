# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'C:/Users/lianjie/.openclaw/workspace/jingcai')

# Test the league mapping
import json
from step8_1923_extractor import _build_league_id_map

m = _build_league_id_map()
print(f'Total mappings: {len(m)}')
print('\nTest lookups:')
for league in ['德甲', '日职', '韩职', '英超', '葡超', '英足总杯', '澳超']:
    print(f'  {league} -> {m.get(league, "NOT FOUND")}')
