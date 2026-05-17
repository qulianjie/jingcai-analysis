# -*- coding: utf-8 -*-
import json

s25_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-03\data\match10_伯恩茅斯__水晶宫\step25_zhuangjia.json'
with open(s25_path, 'r', encoding='utf-8') as f:
    raw = f.read()

print('Raw JSON length: %d' % len(raw))
print('First 200 chars:')
print(raw[:200])
print()
print('Last 200 chars:')
print(raw[-200:])
