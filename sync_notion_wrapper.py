# -*- coding: utf-8 -*-
"""Notion同步包装器 - 调用sync_notion.js"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
node_path = 'node'  # 假设 node 在 PATH 中

# 获取参数
args = sys.argv[1:]
if not args:
    args = ['add']

# 调用 sync_notion.js
cmd = [node_path, os.path.join(SCRIPT_DIR, 'sync_notion.js')] + args
result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, encoding='utf-8', errors='replace')

if result.stdout:
    for line in result.stdout.strip().split('\n'):
        print(line.strip())

if result.returncode != 0:
    print(f'[ERROR] sync_notion.js 返回码: {result.returncode}', file=sys.stderr)
    if result.stderr:
        print(f'[STDERR] {result.stderr[:1000]}', file=sys.stderr)
    sys.exit(result.returncode)
