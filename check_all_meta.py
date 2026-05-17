# -*- coding: utf-8 -*-
import glob, json, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        meta = json.loads(f.read().decode('utf-8'))
    fid = meta.get('fid', '')
    league = meta.get('league', '')
    macau = meta.get('macau_line', '')
    print(f"fid={fid} league={repr(league)} macau={repr(macau)} dir={os.path.basename(d)}")
