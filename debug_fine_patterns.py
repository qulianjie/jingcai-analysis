# -*- coding: utf-8 -*-
"""Debug fine-grained pattern extraction"""
import os, sys, json, glob, re

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

# Test extraction on a single report
date_dir = os.path.join(TASKS_DIR, '2026-05-03')
for fname in os.listdir(date_dir):
    if '001' in fname and fname.endswith('.md'):
        fpath = os.path.join(date_dir, fname)
        content = rd(fpath)
        
        print(f'=== Testing {fname} ===')
        
        # 1. 澳门亚盘
        m = re.search(r'澳门亚盘[：:](.+)', content)
        if m:
            print(f'  澳门亚盘: {m.group(1).strip()}')
        
        # 2. 欧赔盘路
        oupei_pattern = r'\|\s*(竞彩官方|Interwetten|百家平均)\s*\|[\s\d.]+\|\s*([⬇⬆⬉⬊➡→]+)\s*\|'
        for m in re.finditer(oupei_pattern, content):
            print(f'  {m.group(1)} 盘路: {m.group(2).strip()}')
        
        # 3. 盘路基准表
        panlu_pattern = r'\|\s*(竞彩欧赔|Interwetten|百家平均|让球指数)\s*\|\s*([⬇⬆⬉⬊➡→]+)\s*\|'
        for m in re.finditer(panlu_pattern, content):
            print(f'  盘路基准 {m.group(1)}: {m.group(2).strip()}')
        
        # 4. 澳门亚盘同赔
        macau_panlu = re.findall(r'盘口不变\s*(?:降水|升水|水位不变)|升盘\s*(?:降水|升水)|降盘\s*(?:降水|升水)', content)
        if macau_panlu:
            print(f'  澳门亚盘同赔样本: {len(macau_panlu)}')
            panlu_counts = {}
            for pt in macau_panlu:
                panlu_counts[pt] = panlu_counts.get(pt, 0) + 1
            for k, v in panlu_counts.items():
                print(f'    {k}: {v}场')
        
        # 5. 澳门初盘
        m = re.search(r'\|\s*澳门\s*\|\s*(.+?)\s*\|', content)
        if m:
            print(f'  澳门行: {m.group(0)}')
        
        break

print()

# Check combo extraction
import importlib
spec = importlib.util.spec_from_file_location("feedback_learner", r"C:\Users\lianjie\.openclaw\workspace\jingcai\feedback_learner.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Test on report
for fname in os.listdir(date_dir):
    if '001' in fname and fname.endswith('.md'):
        fpath = os.path.join(date_dir, fname)
        content = rd(fpath)
        combo = module.extract_combo_from_report(content)
        print(f'=== Combo extraction for {fname} ===')
        for k, v in combo.items():
            print(f'  {k}: {v}')
        break
