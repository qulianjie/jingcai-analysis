# -*- coding: utf-8 -*-
import os, glob

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15'
for f in sorted(glob.glob(os.path.join(base, '*.md'))):
    name = os.path.basename(f)
    size = os.path.getsize(f)
    print(f'{size:>8}  {name}')
