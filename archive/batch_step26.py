# -*- coding: utf-8 -*-
"""批量补跑step26（盈亏占比分析）"""
import os, sys, time, subprocess

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

BASE = 'jingcai/tasks'
SCRIPT_DIR = 'jingcai'

# 找出所有有step25但缺step26的日期
dates_to_run = set()
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    has_s25 = False
    has_s26 = False
    for m in os.listdir(data_dir):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp):
            continue
        s25 = os.path.join(mp, 'step25_zhuangjia.json')
        s26 = os.path.join(mp, 'step26_profit_ratio.json')
        if os.path.exists(s25) and os.path.getsize(s25) > 0:
            has_s25 = True
        if os.path.exists(s26) and os.path.getsize(s26) > 0:
            has_s26 = True
    
    if has_s25 and not has_s26:
        dates_to_run.add(d)

print(f'需要补跑step26的日期: {len(dates_to_run)}个')
for dt in sorted(dates_to_run):
    print(f'  {dt}')

# 逐日跑step26
for dt in sorted(dates_to_run):
    print(f'\n>>> 跑 {dt} 的step26...')
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step26_profit_ratio.py'), dt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                               encoding='utf-8', errors='replace')
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'OK' in line or '完成' in line or '找到' in line:
                    print(f'  {line.strip()}')
        else:
            print(f'  ERR: code={result.returncode}')
            if result.stderr:
                print(f'  STDERR: {result.stderr[:300]}')
    except subprocess.TimeoutExpired:
        print(f'  TIMEOUT: {dt}')
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(2)

# 统计
total_s26 = 0
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp):
            continue
        s26 = os.path.join(mp, 'step26_profit_ratio.json')
        if os.path.exists(s26) and os.path.getsize(s26) > 0:
            total_s26 += 1

print(f'\n总step26: {total_s26}场')
