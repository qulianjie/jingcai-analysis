#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from _league_util import _league_match

cases = [
    ('沙特联', '沙特职业联赛', True, '同一联赛别名'),
    ('沙特甲', '沙特职业联赛', False, '跨级别'),
    ('沙特乙', '沙特职业联赛', False, '跨级别'),
    ('沙特U17', '沙特职业联赛', False, '青年队'),
    ('日职乙', '日职', False, '跨级别'),
    ('瑞典超', '瑞超', True, '同一联赛别名'),
    ('瑞典超甲', '瑞超', False, '跨级别'),
    ('俄超', '白俄超', False, '跨国家'),
    ('白俄超', '俄超', False, '跨国家'),
    ('爱超', '北爱超', False, '跨国家'),
    ('克杯', '乌克杯', False, '跨国家'),
    ('乌克杯', '克杯', False, '跨国家'),
    ('苏足总杯', '英足总杯', False, '跨国家杯赛'),
    ('英超', '英超Premier League', True, '同一联赛简称'),
    ('西甲', '西甲La Liga', True, '同一联赛简称'),
    ('韩职', 'K1联赛', True, '已知别名'),
    ('荷乙', '荷乙', True, '相同'),
    ('葡萄牙超级联赛', '葡超', True, '全称'),
    ('日联', 'J2联赛', True, '日联=J2别名'),
    ('亚冠', '亚洲冠军乙级联赛', False, '跨级别'),
    ('解放者杯', '解放者杯U20', False, '青年队'),
    ('欧罗巴', '欧联U23', False, '青年队'),
]
allok = True
for src, tgt, exp, note in cases:
    got = _league_match(src, tgt)
    ok = got == exp
    if not ok:
        allok = False
    print(f'{"✅" if ok else "❌"} {src} vs {tgt} → {got} (期望{exp}) {note}')
print()
print('全部通过' if allok else '有失败！')
