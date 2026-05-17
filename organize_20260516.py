# -*- coding: utf-8 -*-
"""整理2026-05-16竞彩数据：清理重复，补全所有30场"""
import os, sys, json, subprocess, time, re

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks/2026-05-16')
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Load matches
with open(os.path.join(TASKS_DIR, 'matches_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])

match_map = {}
for m in all_matches:
    num_raw = m.get('matchnum', '')
    m2 = re.search(r'(\d{3})$', num_raw)
    if m2:
        match_map[m2.group(1)] = m

# Build map from match number -> data dir with completeness info
dir_map = {}  # num -> (dir_name, is_ok)
for d in sorted(os.listdir(DATA_DIR)):
    if not d.startswith('match') or not os.path.isdir(os.path.join(DATA_DIR, d)):
        continue
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        mn = meta.get('matchnum', '')
        num = ''
        m2 = re.search(r'(\d{3})$', mn)
        if m2:
            num = m2.group(1)
        
        s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
        s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
        s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
        s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
        s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
        
        is_ok = (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24)
        
        # Prefer if already in map and new one is OK
        if num not in dir_map:
            dir_map[num] = (d, is_ok)
        elif is_ok and not dir_map[num][1]:
            dir_map[num] = (d, is_ok)

# Find next available dir number
max_dir = 0
for d in os.listdir(DATA_DIR):
    if d.startswith('match'):
        n = int(d.split('_')[0].replace('match', ''))
        if n > max_dir:
            max_dir = n
next_dir = max_dir + 1

# Identify what needs work
print('=== 当前数据状态 ===')
needs_work = []
for num in sorted(match_map.keys()):
    if num in dir_map:
        d, is_ok = dir_map[num]
        status = 'OK' if is_ok else 'NEED_FIX'
        m = match_map[num]
        print(f'  {num}: {d[:40]:40s} -> {status} ({m.get("home","")} vs {m.get("away","")})')
        if not is_ok:
            needs_work.append(('FIX', num, d))
    else:
        m = match_map[num]
        print(f'  {num}: MISSING ({m.get("home","")} vs {m.get("away","")})')
        needs_work.append(('CREATE', num, None))

print(f'\n需要处理: {len(needs_work)} 场')

# Process each
for typ, num, old_dir in needs_work:
    m = match_map[num]
    home = m.get('home', '')
    away = m.get('away', '')
    match_num = m.get('matchnum', '')
    
    if typ == 'CREATE':
        dir_name = 'match{}_{}__{}'.format(next_dir, home, away)
        match_dir = os.path.join(DATA_DIR, dir_name)
        os.makedirs(match_dir, exist_ok=True)
        meta = {
            'matchnum': match_num,
            'match': '{} {} vs {}'.format(match_num, home, away),
            'fid': m.get('fid', ''),
            'league': m.get('league', ''),
            'home': home,
            'away': away,
            'date': '2026-05-16',
            'status': 'in_progress',
            'home_id': m.get('home_id', ''),
            'away_id': m.get('away_id', ''),
            'rq': m.get('rq', ''),
            'macau_line': m.get('macau_line', ''),
        }
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        next_dir += 1
        print(f'\n[{num}] 新建目录: {dir_name}')
    else:
        match_dir = os.path.join(DATA_DIR, old_dir)
        print(f'\n[{num}] 修复目录: {old_dir}')
    
    steps = [
        'step146_extractor.py',
        'step235_runner.py',
        'step7_runner.py',
        'step8_1923_extractor.py',
        'step918_extractor.py',
        'step24_extractor.py',
    ]
    
    for script in steps:
        print(f'  -> {script}...')
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPT_DIR, script), match_dir],
                timeout=1800, encoding='utf-8', errors='replace',
                creationflags=0x08000000
            )
            print(f'  rc={r.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  TIMEOUT')
        except Exception as e:
            print(f'  ERROR: {e}')
        time.sleep(1)
    
    print('  -> report...')
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=0x08000000
        )
    except Exception as e:
        print(f'  ERROR: {e}')
    
    time.sleep(1)

# Final: ensure all 30 report directories have their .md file inside
print('\n=== 整理报告目录 ===')
# Reports are currently in TASKS_DIR root as 周日XXX_XXX.md
# They should also be copied into each 周日XXX_XXX/ directory
for f in sorted(os.listdir(TASKS_DIR)):
    fp = os.path.join(TASKS_DIR, f)
    if f.endswith('.md') and f.startswith('周') and f != 'sunday_matches.md':
        # Extract match info
        m = re.match(r'(周[日一二三四五六])(\d{3})_(.+)\.md', f)
        if m:
            day = m.group(1)
            num = m.group(2)
            teams = m.group(3)
            dir_name = f'{day}{num}_{teams}'
            dir_path = os.path.join(TASKS_DIR, dir_name)
            if os.path.isdir(dir_path):
                dest = os.path.join(dir_path, f)
                if not os.path.exists(dest):
                    import shutil
                    shutil.copy2(fp, dest)
                    print(f'  Copied {f} -> {dir_name}/')

# Final summary
print('\n=== 最终状态 ===')
# Count OK data dirs
ok_count = 0
for num in sorted(match_map.keys()):
    if num in dir_map:
        d, is_ok = dir_map[num]
        if is_ok:
            ok_count += 1

print(f'数据目录: {ok_count}/{len(match_map)} OK')

report_files = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and f.startswith('周') and f != 'sunday_matches.md']
print(f'报告文件: {len(report_files)}')

# Remove duplicates
seen_nums = set()
dup_removed = 0
for f in sorted(os.listdir(TASKS_DIR)):
    fp = os.path.join(TASKS_DIR, f)
    if f.endswith('.md') and f.startswith('周日'):
        m2 = re.search(r'(\d{3})', f)
        if m2:
            num = m2.group(1)
            if num in seen_nums:
                os.remove(fp)
                dup_removed += 1
                print(f'  Removed duplicate: {f}')
            else:
                seen_nums.add(num)

print(f'Duplicates removed: {dup_removed}')
