# -*- coding: utf-8 -*-
"""Find Brest vs Strasbourg report"""
import glob, os, sys

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
# 2026-05-13 is Wednesday
for date in ['2026-05-13', '2026-05-14', '2026-05-15']:
    ddir = os.path.join(base, 'tasks', date)
    if not os.path.exists(ddir):
        continue
    for f in sorted(glob.glob(os.path.join(ddir, '*.md'))):
        if 'sunday_matches' in f:
            continue
        try:
            content = open(f, encoding='utf-8').read(1000)
        except:
            continue
        if '\u5e03\u96f7\u65af\u7279' in content or '\u65af\u7279\u62c9\u65af' in content:
            name = os.path.basename(f)
            print(f"FOUND [{date}]: {name}")
            # Print first 5 lines
            full = open(f, encoding='utf-8').read()
            for line in full.split('\n')[:10]:
                print(f"  {line[:80]}")
