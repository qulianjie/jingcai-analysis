# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'C:/Users/lianjie/.openclaw/workspace/jingcai')

from step8_1923_extractor import _league_match

# Test cases
tests = [
    ('日职', '日职'),
    ('日职', 'J1联赛'),
    ('日职', 'J1'),
    ('德甲', '德甲'),
    ('德甲', '德Bundesliga'),
    ('韩职', '韩职'),
    ('韩职', 'K1联赛'),
    ('韩职', 'K联赛'),
    ('澳超', '澳超'),
    ('葡超', '葡超'),
]

for src, tgt in tests:
    result = _league_match(src, tgt)
    print(f'_league_match({repr(src)}, {repr(tgt)}) = {result}')
