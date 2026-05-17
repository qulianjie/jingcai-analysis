# -*- coding: utf-8 -*-
import glob, json, os, sys, subprocess

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 找到 fid=1411377
target_dir = None
for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        meta = json.loads(f.read().decode('utf-8'))
    if meta.get('fid') == '1411377':
        target_dir = d
        print(f"验证: league={repr(meta.get('league'))}, macau_line={repr(meta.get('macau_line'))}")
        break

if not target_dir:
    print("ERROR")
    sys.exit(1)

print(f"\n重新跑 step8_1923...")
result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', target_dir],
    cwd=base,
    timeout=300
)

# 检查结果
step8 = os.path.join(target_dir, 'group03_asian', 'step8_same_league.txt')
step19 = os.path.join(target_dir, 'group06_baijia', 'step19_baijia_compare.txt')

print("\n=== 最终结果 ===")
for fp, label in [(step8, 'Step8'), (step19, 'Step19-23')]:
    if os.path.exists(fp):
        with open(fp, 'rb') as f:
            content = f.read().decode('utf-8')
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        print(f"{label}: {table_rows} table rows ({len(lines)} lines)")
    else:
        print(f"{label}: 文件不存在")
