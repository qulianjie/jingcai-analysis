# -*- coding: utf-8 -*-
"""
回填 5月5号 meta.json 的 macau_line 字段
从 step6_asian_base.txt 中提取澳门亚盘数据
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
    
    # 如果 macau_line 已经有值就跳过
    if meta.get('macau_line', ''):
        print(f"  {d}: macau_line already = {meta['macau_line']}")
        continue
    
    # 从 step6_asian_base.txt 提取澳门亚盘
    step6_file = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
    if not os.path.isfile(step6_file):
        print(f"  {d}: step6 file not found")
        continue
    
    with open(step6_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 找澳门行: | 澳门 | 球半 0.980|0.800 | 球半 0.980|0.800 |
    macau_line = ''
    for line in text.split('\n'):
        if '| 澳门 |' in line:
            # 提取即时盘（第三个字段）
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                # parts[3] is 即时盘, e.g., "球半 0.980|0.800"
                instant = parts[3]
                # 提取纯盘口部分（去掉水位）
                macau_line = re.sub(r'\s+\d[\d.]*\s*\|\s*[\d.]+', '', instant).strip()
            break
    
    if macau_line:
        meta['macau_line'] = macau_line
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"  {d}: macau_line = {macau_line} (matchnum={meta.get('matchnum','')})")
    else:
        print(f"  {d}: macau_line NOT FOUND in step6")
