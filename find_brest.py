# -*- coding: utf-8 -*-
import glob, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
# Search for Wednesday matches with Brest
for f in sorted(glob.glob(os.path.join(base, 'tasks', '**', '*.md'), recursive=True)):
    if 'sunday_matches' in f or '\\data\\' in f:
        continue
    try:
        name = os.path.basename(f).encode('latin-1', errors='replace').decode('latin-1')
    except:
        continue
    if '\u5e03\u96f7\u65af\u7279' in open(f, encoding='utf-8', errors='replace').read(500) and '\u4e09' in name:
        print(f"FOUND: {f}")
        print(f"  Name: {name}")
