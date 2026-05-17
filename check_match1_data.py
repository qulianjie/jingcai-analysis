# -*- coding: utf-8 -*-
"""检查match1的中间数据文件"""
import os, json

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in os.listdir(d):
    if f.startswith('match1_'):
        path = os.path.join(d, f)
        print('=== group01_europe ===')
        g1 = os.path.join(path, 'group01_europe')
        if os.path.isdir(g1):
            for ff in sorted(os.listdir(g1)):
                if ff.endswith('.md') or ff.endswith('.txt'):
                    fp = os.path.join(g1, ff)
                    with open(fp, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for line in content.split('\n')[:20]:
                        print('  %s' % line[:100])
                    print()
        
        print('=== group02_handicap ===')
        g2 = os.path.join(path, 'group02_handicap')
        if os.path.isdir(g2):
            for ff in sorted(os.listdir(g2)):
                if ff.endswith('.md') or ff.endswith('.txt'):
                    fp = os.path.join(g2, ff)
                    with open(fp, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for line in content.split('\n')[:20]:
                        print('  %s' % line[:100])
                    print()
        
        print('=== group03_asian ===')
        g3 = os.path.join(path, 'group03_asian')
        if os.path.isdir(g3):
            for ff in sorted(os.listdir(g3)):
                if ff.endswith('.md') or ff.endswith('.txt'):
                    fp = os.path.join(g3, ff)
                    with open(fp, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for line in content.split('\n')[:20]:
                        print('  %s' % line[:100])
                    print()
