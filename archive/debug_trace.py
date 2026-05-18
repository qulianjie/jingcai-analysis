# -*- coding: utf-8 -*-
"""Debug: trace step8_1923 execution for fid=1411377"""
import glob, json, os, sys, subprocess, tempfile

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
        break

if not target_dir:
    print("ERROR: 找不到 fid=1411377")
    sys.exit(1)

print(f"目标目录: {os.path.basename(target_dir)}")

# 读取 meta.json
with open(os.path.join(target_dir, 'meta.json'), 'rb') as f:
    meta = json.loads(f.read().decode('utf-8'))

print(f"league = {repr(meta.get('league'))}")
print(f"macau_line = {repr(meta.get('macau_line'))}")

# 创建临时脚本，monkey-patch step8_1923 的初始化
script = f'''# -*- coding: utf-8 -*-
import sys
import os

# Monkey-patch to capture initialization
init_league = None
init_macau_line = None

original_print = print
def tracking_print(*args, **kwargs):
    global init_league, init_macau_line
    msg = ' '.join(str(a) for a in args)
    if '联赛ID:' in msg and '->' in msg:
        parts = msg.split('->')
        init_league = parts[0].strip().replace('联赛ID:', '').strip()
        init_macau_line = meta.get('macau_line', '') if hasattr(meta, 'get') else ''
    original_print(msg)

# Now import and run step8_1923
sys.path.insert(0, r'C:\\\\Users\\\\lianjie\\\\.openclaw\\\\workspace\\\\jingcai')
import builtins
builtins.print = tracking_print

# Now set up the module-level variables
import step8_1923_extractor as s8
s8.MATCH_DIR = r'{target_dir}'
s8.LEAGUE = meta.get('league', '')
s8.MACAU_LINE = meta.get('macau_line', '')

print(f"After patch: LEAGUE={repr(s8.LEAGUE)}")
print(f"After patch: MACAU_LINE={repr(s8.MACAU_LINE)}")
'''

# 先删除旧的输出文件
step8_file = os.path.join(target_dir, 'group03_asian', 'step8_same_league.txt')
step19_file = os.path.join(target_dir, 'group06_baijia', 'step19_baijia_compare.txt')

for fp in [step8_file, step19_file]:
    if os.path.exists(fp):
        os.remove(fp)
        print(f"Deleted old file: {fp}")

# 直接调用脚本
print(f"\nRunning with dir: {target_dir}")
result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', target_dir],
    cwd=base,
    timeout=300
)

# 检查结果
print("\n=== Results ===")
for fp, label in [(step8_file, 'Step8'), (step19_file, 'Step19-23')]:
    if os.path.exists(fp):
        size = os.path.getsize(fp)
        with open(fp, 'rb') as f:
            content = f.read().decode('utf-8')
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        print(f"{label}: {table_rows} table rows, {len(lines)} lines, {size} bytes")
        if table_rows > 0:
            print(f"  Sample rows:")
            for l in lines[:6]:
                print(f"    {l[:100]}")
    else:
        print(f"{label}: 文件不存在")
