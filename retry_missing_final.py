# -*- coding: utf-8 -*-
"""补跑最后5个缺失的比赛"""
import sys, os, json, subprocess, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')

# Find dirs missing step8/step9/step14/step19
dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])

targets = []
for d in dirs:
    dp = os.path.join(DATA_DIR, d)
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian/step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) else 0
    ok = s8 > 500 and s9 > 500 and s14 > 500 and s19 > 500
    if not ok:
        targets.append(d)
        print(f'MISS: {d}')
    else:
        print(f'OK:   {d}')

print(f'\n需要补跑: {len(targets)} 个')

for d in targets:
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_path):
        print(f'\nSKIP {d} - no meta.json')
        continue
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print(f'\n{"="*60}')
    print(f'{d}: {meta.get("home","?")} vs {meta.get("away","?")} ({meta.get("league","?")})')
    print(f'{"="*60}')

    # Step 8 + 19-23
    s8_path = os.path.join(dp, 'group03_asian/step8_same_league.txt')
    if not os.path.exists(s8_path) or os.path.getsize(s8_path) < 500:
        print(f'  -> 跑 step8+19-23...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step8+19-23: return={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  step8+19-23: 超时')
        except Exception as e:
            print(f'  step8+19-23: ERROR: {e}')
        time.sleep(2)

    # Step 9-18
    s9_path = os.path.join(dp, 'group04_teamA/step9_home_history.txt')
    if not os.path.exists(s9_path) or os.path.getsize(s9_path) < 500:
        print(f'  -> 跑 step9-18...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step9-18: return={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  step9-18: 超时')
        except Exception as e:
            print(f'  step9-18: ERROR: {e}')
        time.sleep(2)

# Verify
print(f'\n{"="*60}')
print('验证:')
print(f'{"="*60}')
ok_count = 0
for d in targets:
    dp = os.path.join(DATA_DIR, d)
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian/step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) else 0
    ok_flag = s8 > 500 and s9 > 500 and s14 > 500 and s19 > 500
    if ok_flag: ok_count += 1
    print(f'  {"OK" if ok_flag else "MISS"} {d}: s8={s8}B s9={s9}B s14={s14}B s19={s19}B')
print(f'\n完成: {ok_count}/{len(targets)}')
