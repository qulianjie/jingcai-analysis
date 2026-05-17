# -*- coding: utf-8 -*-
import os, json

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data'
for name in sorted(os.listdir(base)):
    path = os.path.join(base, name)
    if os.path.isdir(path):
        meta_path = os.path.join(path, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            print(f"dir={name} | league={meta.get('league')} | home={meta.get('home')} | away={meta.get('away')} | fid={meta.get('fid')} | macau={meta.get('macau_line')}")
