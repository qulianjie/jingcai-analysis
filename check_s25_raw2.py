# -*- coding: utf-8 -*-
import json, os

s25_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-03\data\match10_伯恩茅斯__水晶宫\step25_zhuangjia.json'
with open(s25_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== labels ===')
for k, v in data.get('labels', {}).items():
    print('%s: bet_pct=%s volume=%s profit=%s' % (k, repr(v.get('bet_pct','')), repr(v.get('volume','')), repr(v.get('profit',''))))

print()
print('=== data ===')
for k, v in data.get('data', {}).items():
    print('%s: bet_pct=%s volume=%s profit=%s' % (k, repr(v.get('bet_pct','')), repr(v.get('volume','')), repr(v.get('profit',''))))
