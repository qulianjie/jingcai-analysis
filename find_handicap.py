# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'jingcai\tasks\2026-05-03\周日011_萨索洛vsAC米兰.md', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.split('\n')
for i, line in enumerate(lines):
    if '让球' in line or '推荐' in line:
        print('Line ' + str(i) + ': ' + line.strip())
