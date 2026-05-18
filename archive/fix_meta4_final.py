# -*- coding: utf-8 -*-
import glob, json, os

# 用 glob 找到 match4 目录
dirs = glob.glob(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data\match4*')
if not dirs:
    print("ERROR: 找不到 match4 目录")
    exit(1)

match_dir = dirs[0]
meta_path = os.path.join(match_dir, 'meta.json')

print(f"目录: {match_dir}")

# 更新 league
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

print(f"更新前: league={repr(meta.get('league'))}, macau_line={repr(meta.get('macau_line'))}")

meta['league'] = '西甲'
meta['macau_line'] = '一球/半球'

with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"更新后: league={repr(meta.get('league'))}, macau_line={repr(meta.get('macau_line'))}")
print()
print(json.dumps(meta, ensure_ascii=False, indent=2))
