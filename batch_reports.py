# -*- coding: utf-8 -*-
"""为所有已有组数据但缺最终报告的比赛生成报告，然后同步Notion"""
import os, sys, json, subprocess, time

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

BASE = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
SCRIPTS = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

def has_any_group(match_dir):
    groups = ['group01_europe', 'group02_handicap', 'group03_asian',
              'group04_teamA', 'group05_teamB', 'group06_baijia']
    for g in groups:
        if os.path.isdir(os.path.join(match_dir, g)):
            return True
    return False

def find_match_dirs(date_dir):
    data_dir = os.path.join(date_dir, 'data')
    if not os.path.isdir(data_dir):
        return []
    matches = []
    for item in sorted(os.listdir(data_dir)):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and item.startswith('match'):
            matches.append(item_path)
    return matches

def has_report(match_dir):
    """Check if a final report .md file exists in parent dir"""
    parent = os.path.dirname(os.path.dirname(match_dir))
    match_name = os.path.basename(match_dir)
    for f in os.listdir(parent):
        if f.endswith('.md') and match_name in f:
            report_path = os.path.join(parent, f)
            if os.path.getsize(report_path) > 1000:
                return True
    return False

def run_script(script_name, args_list, timeout=300):
    script_path = os.path.join(SCRIPTS, script_name)
    if not os.path.exists(script_path):
        print(f'    ❌ 脚本不存在: {script_name}')
        return False
    try:
        r = subprocess.run(
            [sys.executable, script_path] + args_list,
            timeout=timeout, encoding='utf-8', errors='replace',
            creationflags=0x08000000, cwd=SCRIPTS
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f'    ⏰ 超时 ({timeout}s)')
        return False
    except Exception as e:
        print(f'    ❌ 错误: {e}')
        return False

print('=' * 70)
print(f'批量生成最终报告 - {time.strftime("%Y-%m-%d %H:%M")}')
print('=' * 70)

# Collect all dates with data
all_dates = set()
for entry in os.listdir(BASE):
    if entry.startswith('2026-'):
        all_dates.add(entry)

# Filter to dates that have match dirs with groups
dates_to_process = []
for date_str in sorted(all_dates):
    date_dir = os.path.join(BASE, date_str)
    match_dirs = find_match_dirs(date_dir)
    has_data = False
    for md in match_dirs:
        if has_any_group(md):
            has_data = True
            break
    if has_data:
        dates_to_process.append(date_str)

print(f'发现 {len(dates_to_process)} 个日期有数据')

report_ok = 0
report_fail = 0
total = 0
synced_dates = set()

for date_str in dates_to_process:
    date_dir = os.path.join(BASE, date_str)
    match_dirs = find_match_dirs(date_dir)
    
    # Find matches with groups but no valid report
    need_report = []
    for md in match_dirs:
        if has_any_group(md):
            if not has_report(md):
                need_report.append(md)
    
    if not need_report:
        print(f'\n{date_str}: 所有比赛已有报告 ✓')
        continue
    
    print(f'\n{date_str}: {len(need_report)} 场比赛需生成报告')
    
    for match_dir in need_report:
        meta_path = os.path.join(match_dir, 'meta.json')
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            home = meta.get('home', '?')
            away = meta.get('away', '?')
        except:
            home, away = '?', '?'
        
        total += 1
        print(f'\n[{date_str}] {total}. {home} vs {away}')
        
        if run_script('final_report_generator.py', [match_dir], timeout=300):
            print(f'  ✅ 报告成功')
            report_ok += 1
        else:
            print(f'  ❌ 报告失败')
            report_fail += 1
        
        synced_dates.add(date_str)
        time.sleep(1)

print(f'\n{"=" * 70}')
print(f'报告生成完成: 成功 {report_ok}, 失败 {report_fail}, 总计 {total}')

print(f'\n{"=" * 70}')
print(f'同步到 Notion...')
print(f'{"=" * 70}')

sync_ok = 0
sync_fail = 0
for date_str in sorted(synced_dates):
    print(f'\n  → 同步 {date_str}...')
    try:
        r = subprocess.run(
            ['node', os.path.join(SCRIPTS, 'pipeline.js'), 'sync', date_str],
            timeout=300, encoding='utf-8', errors='replace',
            creationflags=0x08000000, cwd=SCRIPTS
        )
        if r.returncode == 0:
            print(f'    ✅ {date_str} 同步成功')
            sync_ok += 1
        else:
            print(f'    ❌ {date_str} 同步失败 (rc={r.returncode})')
            sync_fail += 1
    except Exception as e:
        print(f'    ❌ {date_str} 同步错误: {e}')
        sync_fail += 1
    time.sleep(3)

print(f'\n{"=" * 70}')
print(f'全部完成!')
print(f'{"=" * 70}')
print(f'报告: 成功 {report_ok}, 失败 {report_fail}')
print(f'同步: 成功 {sync_ok}, 失败 {sync_fail}')
print(f'{"=" * 70}')
