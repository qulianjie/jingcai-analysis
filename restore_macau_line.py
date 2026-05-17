# -*- coding: utf-8 -*-
"""从step6_asian_base.txt提取澳门即时盘，补全meta.json的macau_line字段"""
import os, json, re

BASE = 'jingcai/tasks'
total = 0
updated = 0
found = 0
missing = 0

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    date_updated = 0
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not (os.path.isdir(mp) and m.startswith('match')):
            continue
        
        meta_path = os.path.join(mp, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        existing_macau = meta.get('macau_line', '')
        
        # 已有且非空，跳过
        if existing_macau:
            continue
        
        total += 1
        
        step6_path = os.path.join(mp, 'group03_asian', 'step6_asian_base.txt')
        macau_line = ''
        
        if os.path.exists(step6_path):
            content = open(step6_path, 'r', encoding='utf-8', errors='replace').read()
            # 匹配整行: | 澳门 | 半球 1.040|0.800 | 半球/一球 升 1.000|0.840 |
            # 用更精确的正则匹配澳门行 + 即时盘部分
            m = re.search(r'\|\s*澳门\s*\|\s*(?:[\u4e00-\u9fff]+/?[\u4e00-\u9fff]*\s*[\d.]+\|[\d.]+)\s*\|\s*([\u4e00-\u9fff]+(?:/[\u4e00-\u9fff]+)?)\s*([升降]?)\s*[\d.]+\|[\d.]+', content)
            if m:
                macau_line = m.group(1).strip()
                if m.group(2):
                    macau_line += ' ' + m.group(2)
        
        if not macau_line:
            missing += 1
            continue
        
        found += 1
        meta['macau_line'] = macau_line
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        updated += 1
        date_updated += 1
    
    if date_updated > 0:
        print(f'  {d}: 更新{date_updated}场')

print(f'\n扫描: {total}场缺macau_line')
print(f'找到: {found}场')
print(f'缺失: {missing}场')
print(f'已更新: {updated}场')
