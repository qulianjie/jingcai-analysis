# -*- coding: utf-8 -*-
"""
Check match data structure - find prediction info
"""
import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check a sample match from May 1
date_dir = r"C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-01"

# Check data dir
data_dir = os.path.join(date_dir, "data")
for d in os.listdir(data_dir):
    if d.startswith("match"):
        match_dir = os.path.join(data_dir, d)
        print(f"\n=== {d} ===")
        for f in sorted(os.listdir(match_dir)):
            fpath = os.path.join(match_dir, f)
            if os.path.isfile(fpath):
                fsize = os.path.getsize(fpath)
                print(f"  {f} ({fsize} bytes)")
                if f.endswith('.json'):
                    try:
                        with open(fpath, 'r', encoding='utf-8') as fp:
                            content = json.load(fp)
                            print(f"    Content: {json.dumps(content, ensure_ascii=False)[:300]}")
                    except:
                        pass
                elif f.endswith('.md') and fsize < 3000:
                    try:
                        with open(fpath, 'r', encoding='utf-8') as fp:
                            lines = fp.readlines()
                            for line in lines[:15]:
                                print(f"    {line.rstrip()}")
                    except:
                        pass
        break

# Also check a match report from root
md_files = [f for f in os.listdir(date_dir) if f.endswith('.md') and not f.startswith('sunday') and not f.startswith('TEMPLATE')]
if md_files:
    sample_md = md_files[1] if len(md_files) > 1 else md_files[0]
    print(f"\n=== Sample report: {sample_md} ===")
    with open(os.path.join(date_dir, sample_md), 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
        for line in lines[:50]:
            print(f"  {line.rstrip()}")
