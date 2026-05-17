import os, json, re

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# 1. List all report files
reports = []
for f in os.listdir(TASKS_DIR):
    if f.endswith('.md') and f.startswith('周') and f != 'sunday_matches.md':
        reports.append(f)
reports.sort()

print(f'=== 报告文件: {len(reports)} 份 ===')
report_nums = set()
for r in reports:
    # Extract match number (e.g., 周日001 -> 001)
    m = re.search(r'(\d{3})', r)
    if m:
        num = m.group(1)
        report_nums.add(num)
        size = os.path.getsize(os.path.join(TASKS_DIR, r))
        print(f'  {num}: {size:>7}B')

# 2. List all data dirs
print(f'\n=== 数据目录: ===')
data_dirs = []
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
        
        # Check completeness
        s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
        s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
        s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
        s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
        s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
        
        ok = 'OK' if (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24) else 'INCOMPLETE'
        print(f'  {d[:50]:50s} -> {num} [{ok}]')
        data_dirs.append((d, num, ok))

# 3. Find missing
print(f'\n=== 缺失分析 ===')
dir_nums = {d[1] for d in data_dirs}

missing_from_data = sorted(report_nums - dir_nums)
missing_from_reports = sorted(dir_nums - report_nums)

if missing_from_data:
    print(f'有报告但缺少数据目录: {missing_from_data}')
if missing_from_reports:
    print(f'有数据目录但缺少报告: {missing_from_reports}')

# 4. Check report directories (not just files)
print(f'\n=== 报告目录 ===')
report_dirs = []
for d in sorted(os.listdir(TASKS_DIR)):
    dp = os.path.join(TASKS_DIR, d)
    if os.path.isdir(dp) and d.startswith('周'):
        report_dirs.append(d)
        files = os.listdir(dp)
        md_files = [f for f in files if f.endswith('.md')]
        print(f'  {d}: {len(files)} 文件, {len(md_files)} .md')

print(f'\n总计: {len(report_dirs)} 个报告目录')
