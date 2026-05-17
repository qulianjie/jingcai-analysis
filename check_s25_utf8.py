# -*- coding: utf-8 -*-
import json

s25_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-03\data\match10_伯恩茅斯__水晶宫\step25_zhuangjia.json'
with open(s25_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for k, v in data.get('labels', {}).items():
    bp = v.get('bet_pct', '')
    vol = v.get('volume', '')
    pro = v.get('profit', '')
    print('%s: bet_pct=%s (len=%d) volume=%s (len=%d) profit=%s (len=%d)' % (
        k.encode('utf-8','replace'), 
        bp.encode('utf-8','replace'), len(bp),
        vol.encode('utf-8','replace'), len(vol),
        pro.encode('utf-8','replace'), len(pro)))
