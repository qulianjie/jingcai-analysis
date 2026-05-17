# -*- coding: utf-8 -*-
import os, json, sys

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data'
match_dir = None
for name in sorted(os.listdir(base)):
    path = os.path.join(base, name)
    if os.path.isdir(path):
        meta_path = os.path.join(path, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            if meta.get('fid') == '1411377':
                match_dir = path
                print(f"找到match4: {name}")
                print(f"  league={meta.get('league')}")
                print(f"  home_id={meta.get('home_id')}")
                print(f"  away_id={meta.get('away_id')}")
                print(f"  fid={meta.get('fid')}")
                print(f"  macau_line={meta.get('macau_line')}")
                break

if not match_dir:
    print("ERROR: 找不到fid=1411377")
    sys.exit(1)

# 看看现有数据
step8 = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
step19 = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')

print()
for fpath, label in [(step8, 'Step8'), (step19, 'Step19-23')]:
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        print(f"{label}: {size} bytes, {len(lines)} lines, {table_rows} table rows")
        if table_rows == 0:
            print(f"  WARNING: 数据为空!")
    else:
        print(f"{label}: 文件不存在")

print()
print("开始重新跑 step8_1923_extractor.py...")
print()

# 重新跑
import subprocess
result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', match_dir],
    cwd=r'C:\Users\lianjie\.openclaw\workspace\jingcai',
    capture_output=False
)

print()
print("=" * 60)
print("重新跑完后检查数据:")
print("=" * 60)

for fpath, label in [(step8, 'Step8'), (step19, 'Step19-23')]:
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        print(f"{label}: {size} bytes, {len(lines)} lines, {table_rows} table rows")
        if table_rows == 0:
            print(f"  WARNING: 仍然为空!")
            print()
            print("--- 文件内容前20行 ---")
            for l in lines[:20]:
                print(f"  {l}")
    else:
        print(f"{label}: 文件不存在")
