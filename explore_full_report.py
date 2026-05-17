# -*- coding: utf-8 -*-
"""探索报告完整结构"""
import os, sys

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(path, 'r', encoding='gbk') as f:
                return f.read()
        except:
            return ''

# 读取一个完整的单场比赛报告
date_dir = os.path.join(TASKS_DIR, '2026-05-03')
for fname in os.listdir(date_dir):
    if fname.endswith('.md') and '001' in fname:
        fpath = os.path.join(date_dir, fname)
        content = rd(fpath)
        print(f'=== {fname} (总行数: {len(content.splitlines())}) ===')
        print()
        # 显示所有行
        for i, line in enumerate(content.splitlines()):
            print(f'{i+1:4d} | {line}')
        break
