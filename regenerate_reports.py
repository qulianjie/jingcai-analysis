# -*- coding: utf-8 -*-
"""批量重新生成所有match的最终报告，标准命名：周X0XX_主队vs客队.md"""
import os, subprocess, json

data_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-09\data'
parent_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-09'
generator = r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_report_generator.py'

matches = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
print(f'找到 {len(matches)} 场比赛')

success = 0
fail = 0

for m in matches:
    match_dir = os.path.join(data_dir, m)
    
    # 从meta.json读取matchnum
    meta_path = os.path.join(match_dir, 'meta.json')
    if not os.path.exists(meta_path):
        print(f'  SKIP: {m} (no meta.json)')
        fail += 1
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    matchnum = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    
    if not matchnum or not home or not away:
        print(f'  SKIP: {m} (incomplete meta)')
        fail += 1
        continue
    
    report_name = f'{matchnum}_{home}vs{away}.md'
    output_path = os.path.join(parent_dir, report_name)
    
    try:
        result = subprocess.run(
            ['python', generator, match_dir, output_path],
            capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            print(f'  OK: {m} -> {report_name}')
            success += 1
        else:
            print(f'  FAIL: {m} - {result.stderr[:100]}')
            fail += 1
    except Exception as e:
        print(f'  ERROR: {m} - {e}')
        fail += 1

print(f'\n完成: 成功{success} 失败{fail}')
