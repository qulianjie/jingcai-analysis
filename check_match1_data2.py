# -*- coding: utf-8 -*-
"""检查match1中间数据"""
import os, json

match_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data\match1_山形飞行__FC大阪'
if not os.path.isdir(match_dir):
    # try find it
    d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
    for f in os.listdir(d):
        if f.startswith('match1_'):
            match_dir = os.path.join(d, f)
            break

print('Match dir: %s' % match_dir)

# Walk all files
for root, dirs, files in os.walk(match_dir):
    for fname in sorted(files):
        fpath = os.path.join(root, fname)
        rel = os.path.relpath(fpath, match_dir)
        print('\n=== %s ===' % rel)
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                content = fh.read()
            if fname.endswith('.json'):
                data = json.loads(content)
                if isinstance(data, dict):
                    for k, v in data.items():
                        print('  %s: %s' % (k, str(v)[:200]))
            else:
                for line in content.split('\n')[:30]:
                    line_clean = ''.join(c for c in line if ord(c) < 0x10000)
                    print('  %s' % line_clean[:120])
        except Exception as e:
            print('  ERROR: %s' % e)
