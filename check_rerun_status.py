# -*- coding: utf-8 -*-
"""
检查几个失败match的step8是否有数据了
"""
import os

test_matches = [
    ('2026-05-12', 'match10_赫塔费__马洛卡'),
    ('2026-05-08', 'match12_莱万特__奥萨苏纳'),
    ('2026-05-08', 'match10_朗斯__南特'),
]

for date, name in test_matches:
    base = 'jingcai/tasks/%s/data/%s' % (date, name)
    step8 = os.path.join(base, 'group03_asian', 'step8_same_league.txt')
    step19 = os.path.join(base, 'group06_baijia', 'step19_baijia_compare.txt')
    
    s8_size = os.path.getsize(step8) if os.path.exists(step8) else 0
    s19_size = os.path.getsize(step19) if os.path.exists(step19) else 0
    
    s8_ts = os.path.getmtime(step8) if os.path.exists(step8) else 0
    s19_ts = os.path.getmtime(step19) if os.path.exists(step19) else 0
    
    import time
    s8_time = time.strftime('%H:%M', time.localtime(s8_ts)) if s8_ts else '?'
    s19_time = time.strftime('%H:%M', time.localtime(s19_ts)) if s19_ts else '?'
    
    print('%s/%s: step8=%d(%s) step19=%d(%s)' % (date, name, s8_size, s8_time, s19_size, s19_time))
