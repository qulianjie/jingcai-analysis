# -*- coding: utf-8 -*-
"""Check meta.json raw bytes for fid=1411377"""
import glob, json, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        raw = f.read()
    meta = json.loads(raw.decode('utf-8'))
    if meta.get('fid') == '1411377':
        print(f"Dir: {os.path.basename(d)}")
        # Find league in raw bytes
        idx = raw.find(b'"league"')
        if idx >= 0:
            print(f"Raw bytes around league: {raw[idx:idx+40]}")
        print(f"league = {repr(meta.get('league'))}")
        print(f"macau_line = {repr(meta.get('macau_line'))}")
        print(f"home = {repr(meta.get('home'))}")
        print(f"away = {repr(meta.get('away'))}")
