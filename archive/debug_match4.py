# -*- coding: utf-8 -*-
"""Debug: run step8_1923 for fid=1411377 with explicit logging"""
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

print(f"目标目录: {target_dir}")
print(f"目录名: {os.path.basename(target_dir)}")

# 读取 meta.json
with open(os.path.join(target_dir, 'meta.json'), 'rb') as f:
    meta = json.loads(f.read().decode('utf-8'))

print(f"meta: league={repr(meta.get('league'))}")
print(f"meta: macau_line={repr(meta.get('macau_line'))}")
print(f"meta: home_id={repr(meta.get('home_id'))}")
print(f"meta: away_id={repr(meta.get('away_id'))}")

# 创建临时脚本，直接调用 step8_1923 的函数
debug_script = '''# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\\Users\\lianjie\\.openclaw\\workspace\\jingcai')

# Import and run step8_1923 with the correct match_dir
from step8_1923_extractor import *

print(f"DEBUG: MATCH_DIR = {repr(MATCH_DIR)}")
print(f"DEBUG: LEAGUE = {repr(LEAGUE)}")
print(f"DEBUG: MACAU_LINE = {repr(MACAU_LINE)}")
'''

# 用子进程跑，确保使用正确的 meta.json
print(f"\nRunning step8_1923_extractor.py with dir: {target_dir}")
result = subprocess.run(
    [sys.executable, '-u', 'step8_1923_extractor.py', target_dir],
    cwd=base,
    capture_output=True,
    text=True,
    timeout=300
)

print("STDOUT:")
print(result.stdout[:3000] if len(result.stdout) > 3000 else result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr[:1000])
print(f"\nReturn code: {result.returncode}")
