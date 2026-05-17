# -*- coding: utf-8 -*-
"""检查各步骤文件的实际内容结构"""
import os, json, re

match_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in sorted(os.listdir(match_dir)):
    if not f.startswith('match1_'):
        continue
    md = os.path.join(match_dir, f)
    print('=== Match dir: %s ===' % f)
    
    for root, dirs, files in os.walk(md):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, md)
            print('\n--- %s ---' % rel)
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                
                if fname.endswith('.json'):
                    data = json.loads(content)
                    if isinstance(data, dict):
                        for k, v in list(data.items())[:5]:
                            print('  %s: %s' % (k, str(v)[:150]))
                else:
                    # Print first 15 lines, strip non-ascii-safe chars
                    for line in content.split('\n')[:15]:
                        safe = ''.join(c if ord(c) < 128 else '?' for c in line)
                        print('  %s' % safe[:120])
            except Exception as e:
                print('  ERROR: %s' % e)
