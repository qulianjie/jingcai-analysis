# -*- coding: utf-8 -*-
"""探索报告中所有可用的精细数据"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# 1. 完整读取一个报告，看所有可用的数据结构
for date in ['2026-05-03']:
    date_dir = os.path.join(TASKS_DIR, date)
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        content = rd(f)
        print(f'=== {os.path.basename(f)} ===')
        print(content[:3000])
        print('...\n')
        break

# 2. 检查 step1 (欧赔基础) 的数据结构
for date in ['2026-05-03']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    for md in sorted(os.listdir(data_dir))[:2]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        
        # Check group01_europe
        g1_dir = os.path.join(md_path, 'group01_europe')
        if os.path.exists(g1_dir):
            for fname in os.listdir(g1_dir):
                fpath = os.path.join(g1_dir, fname)
                content = rd(fpath)
                print(f'\n=== {md}/group01_europe/{fname} ===')
                print(content[:800])
        
        # Check group02_handicap
        g2_dir = os.path.join(md_path, 'group02_handicap')
        if os.path.exists(g2_dir):
            for fname in os.listdir(g2_dir):
                fpath = os.path.join(g2_dir, fname)
                content = rd(fpath)
                print(f'\n=== {md}/group02_handicap/{fname} ===')
                print(content[:800])
        
        # Check group03_asian
        g3_dir = os.path.join(md_path, 'group03_asian')
        if os.path.exists(g3_dir):
            for fname in os.listdir(g3_dir):
                fpath = os.path.join(g3_dir, fname)
                content = rd(fpath)
                print(f'\n=== {md}/group03_asian/{fname} ===')
                print(content[:800])
        
        break
