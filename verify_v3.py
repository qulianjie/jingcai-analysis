# -*- coding: utf-8 -*-
import os, json
d = r'jingcai\tasks\2026-05-05\data'
for m in sorted(os.listdir(d)):
    p = os.path.join(d, m, 'meta.json')
    if not os.path.isfile(p): continue
    meta = json.load(open(p, encoding='utf-8'))
    s8 = os.path.join(d, m, 'group03_asian', 'step8_same_league.txt')
    s19 = os.path.join(d, m, 'group06_baijia', 'step19_baijia_compare.txt')
    c8 = open(s8, encoding='utf-8').read() if os.path.isfile(s8) else ''
    c19 = open(s19, encoding='utf-8').read() if os.path.isfile(s19) else ''
    rows8 = sum(1 for l in c8.split('\n') if l.startswith('| ') and '序号' not in l)
    rows19 = sum(1 for l in c19.split('\n') if l.startswith('| ') and '赛事' not in l)
    print(f"{meta['matchnum']} {meta['home']}vs{meta['away']} | {meta['league']} | macau={meta['macau_line']} | step8={rows8} rows | step19={rows19} rows")
