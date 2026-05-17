# -*- coding: utf-8 -*-
import os
BASE = 'jingcai/tasks'
total = 0
by_date = {}
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    count = 0
    for m in os.listdir(data_dir):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp):
            continue
        s26 = os.path.join(mp, 'step26_profit_ratio.json')
        if os.path.exists(s26) and os.path.getsize(s26) > 0:
            count += 1
            total += 1
    if count > 0:
        by_date[d] = count

print(f'总step26: {total}场')
for dt, cnt in sorted(by_date.items()):
    print(f'  {dt}: {cnt}场')
