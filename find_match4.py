# -*- coding: utf-8 -*-
import glob, json, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

all_match4 = glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match4*'))
print(f"找到 {len(all_match4)} 个 match4 目录:")

for d in all_match4:
    meta_path = os.path.join(d, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        fid = meta.get('fid', '')
        league = meta.get('league', '')
        macau = meta.get('macau_line', '')
        print(f"  fid={fid}, league={repr(league)}, macau={repr(macau)}")
        print(f"  dir={d}")
