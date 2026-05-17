# -*- coding: utf-8 -*-
"""补跑缺失的step8/step9-23步骤"""
import os, sys, json, time, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16/data')

def log(tag, msg):
    print(f'[{tag}] {msg}')

def run_script(script, args, timeout=3600):
    sp = os.path.join(SCRIPT_DIR, script)
    cmd = [sys.executable, sp] + args
    log('RUN', f'{script} {" ".join(args)}')
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding='utf-8', errors='replace')
        if r.returncode != 0:
            log('ERR', f'{script} 返回码 {r.returncode}')
            if r.stderr:
                log('STDERR', r.stderr[:500])
            return False
        if r.stdout:
            for line in r.stdout.strip().split('\n')[-3:]:
                log('OUT', line.strip())
        return True
    except subprocess.TimeoutExpired:
        log('ERR', f'{script} 超时')
        return False
    except Exception as e:
        log('ERR', f'{script} 异常: {e}')
        return False

# Get all match dirs
dirs = sorted([d for d in os.listdir(DATA_DIR) 
               if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])

print(f'共 {len(dirs)} 个比赛目录')

missing_steps = []
for d in dirs:
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if not os.path.exists(meta_path):
        log('SKIP', f'{d} 无meta.json')
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    needs_s8 = not os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt'))
    needs_s9 = not os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt'))
    needs_s14 = not os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt'))
    needs_s19 = not os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt'))
    
    if needs_s8 or needs_s9 or needs_s14 or needs_s19:
        missing_steps.append((d, dp, meta, needs_s8, needs_s9, needs_s14, needs_s19))
        print(f'  {d}: s8={needs_s8} s9={needs_s9} s14={needs_s14} s19={needs_s19}')

print(f'\n需要补跑: {len(missing_steps)} 个目录')
print('开始补跑...\n')

for i, (d, dp, meta, need_s8, need_s9, need_s14, need_s19) in enumerate(missing_steps, 1):
    print(f'\n{"="*60}')
    print(f'[{i}/{len(missing_steps)}] {d} ({meta.get("home","")} vs {meta.get("away","")})')
    print(f'{"="*60}')
    
    # Step 8 + 19-23
    if need_s8 or need_s19:
        run_script('step8_1923_extractor.py', [dp], timeout=3600)
        time.sleep(2)
    
    # Step 9-18
    if need_s9 or need_s14:
        run_script('step918_extractor.py', [dp], timeout=3600)
        time.sleep(2)

print(f'\n{"="*60}')
print('补跑完成！')
print(f'{"="*60}')

# Re-check
print('\n重新检查结果...')
for d, dp, meta, _, _, _, _ in missing_steps:
    s8 = os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt'))
    s9 = os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt'))
    s14 = os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt'))
    s19 = os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt'))
    status = 'OK' if all([s8, s9, s14, s19]) else 'MISSING'
    print(f'  {status} {d}: s8={s8} s9={s9} s14={s14} s19={s19}')
