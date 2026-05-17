# -*- coding: utf-8 -*-
"""
回填 5月5号 meta.json 的 macau_line 字段
从 step6_asian_base.txt 中提取澳门亚盘数据（纯盘口，不含水位）
"""
import os, sys, re, json
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data_dir = r'jingcai\tasks\2026-05-05\data'

for d in sorted(os.listdir(data_dir)):
    match_dir = os.path.join(data_dir, d)
    if not os.path.isdir(match_dir):
        continue
    
    meta_file = os.path.join(match_dir, 'meta.json')
    if not os.path.isfile(meta_file):
        continue
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    # 从 step6_asian_base.txt 提取澳门亚盘
    step6_file = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
    if not os.path.isfile(step6_file):
        continue
    
    with open(step6_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 找澳门行: | 澳门 | 球半 0.980|0.800 | 球半 0.980|0.800 |
    macau_line = ''
    for line in text.split('\n'):
        if '| 澳门 |' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                # parts[3] is 即时盘, e.g., "球半 0.980|0.800"
                instant = parts[3]
                # Remove all digit patterns and | separators, keep only Chinese chars
                macau_line = re.sub(r'[\d.|\s]+', '', instant).strip()
                # Also remove 升/降 markers that might have spaces
                macau_line = macau_line.strip()
            break
    
    if macau_line:
        meta['macau_line'] = macau_line
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"  {d}: macau_line = {macau_line} ({meta.get('matchnum','')})")
    else:
        print(f"  {d}: NOT FOUND ({meta.get('matchnum','')})")
