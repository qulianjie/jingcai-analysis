# -*- coding: utf-8 -*-
"""补跑缺失的 step8/step9-18 步骤"""
import sys, os, json, subprocess, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')

# Find missing dirs
dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match')])
missing = []
for d in dirs:
    dp = os.path.join(DATA_DIR, d)
    s8 = os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt'))
    s9 = os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt'))
    s14 = os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt'))
    s19 = os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt'))
    if not s8 or not s9 or not s14 or not s19:
        missing.append(d)

print(f'需要补跑: {len(missing)} 个目录')

for i, d in enumerate(missing, 1):
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_path):
        print(f'\n[{i}/{len(missing)}] SKIP {d} - no meta.json')
        continue

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    home = meta.get('home', '?')
    away = meta.get('away', '?')
    league = meta.get('league', '?')
    print(f'\n{"="*60}')
    print(f'[{i}/{len(missing)}] {home} vs {away} ({league})')
    print(f'{"="*60}')

    # Step 8 + 19-23
    s8_path = os.path.join(dp, 'group03_asian/step8_same_league.txt')
    if not os.path.exists(s8_path):
        print(f'  -> 跑 step8+19-23...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step8+19-23: return={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  step8+19-23: 超时(1800s)')
        except Exception as e:
            print(f'  step8+19-23: ERROR: {e}')
        time.sleep(2)
    else:
        print(f'  step8 已存在: {os.path.getsize(s8_path)}B')

    # Step 9-18
    s9_path = os.path.join(dp, 'group04_teamA/step9_home_history.txt')
    if not os.path.exists(s9_path):
        print(f'  -> 跑 step9-18...')
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, 'step918_extractor.py'), dp]
        try:
            r = subprocess.run(cmd, timeout=1800, encoding='utf-8', errors='replace')
            print(f'  step9-18: return={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  step9-18: 超时(1800s)')
        except Exception as e:
            print(f'  step9-18: ERROR: {e}')
        time.sleep(2)
    else:
        print(f'  step9 已存在: {os.path.getsize(s9_path)}B')

# Verify
print(f'\n{"="*60}')
print('验证结果:')
print(f'{"="*60}')
ok_count = 0
for d in missing:
    dp = os.path.join(DATA_DIR, d)
    s8p = os.path.join(dp, 'group03_asian/step8_same_league.txt')
    s9p = os.path.join(dp, 'group04_teamA/step9_home_history.txt')
    s14p = os.path.join(dp, 'group05_teamB/step14_away_history.txt')
    s19p = os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')
    s8s = os.path.getsize(s8p) if os.path.exists(s8p) else 0
    s9s = os.path.getsize(s9p) if os.path.exists(s9p) else 0
    s14s = os.path.getsize(s14p) if os.path.exists(s14p) else 0
    s19s = os.path.getsize(s19p) if os.path.exists(s19p) else 0
    ok = s8s > 500 and s9s > 500 and s14s > 500 and s19s > 500
    tag = 'OK' if ok else 'MISSING'
    if ok: ok_count += 1
    print(f'  {tag} {d}: s8={s8s}B s9={s9s}B s14={s14s}B s19={s19s}B')

print(f'\n补跑完成: {ok_count}/{len(missing)} 成功')
