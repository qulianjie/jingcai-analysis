# -*- coding: utf-8 -*-
import json, os, sys

# Read the raw JSON bytes
s25_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-03\data\match10_伯恩茅斯__水晶宫\step25_zhuangjia.json'
with open(s25_path, 'r', encoding='utf-8') as f:
    raw = f.read()

# Find the labels section
import re
# Look for bet_pct values in labels
labels_section = raw[raw.find('"labels"'):raw.find('"data"')]
print('Labels section (first 500 chars):')
print(labels_section[:500])
print()

# Extract bet_pct values
matches = re.findall(r'"bet_pct":\s*"([^"]*)"', labels_section)
print('bet_pct values: %s' % [repr(m) for m in matches])
