import os

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Reports in tasks dir
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and f.startswith('周日')]
print(f'Reports: {len(reports)}')
report_nums = set()
for r in sorted(reports):
    num = r[2:5]  # e.g. 001
    report_nums.add(num)
    size = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {num}: {r[:50]:50s} {size}B')

# Data dirs
print(f'\nData dirs: ')
data_dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])
print(f'  Total: {len(data_dirs)}')

# Load meta for each
import json
dir_match_nums = {}
for d in data_dirs:
    dp = os.path.join(DATA_DIR, d)
    meta_path = os.path.join(dp, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        mn = meta.get('matchnum', '')
        num = ''
        import re
        m2 = re.search(r'(\d{3})$', mn)
        if m2:
            num = m2.group(1)
        dir_match_nums[d] = num
        s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
        s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
        s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
        s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
        s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
        ok = 'OK' if (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24) else 'INCOMPLETE'
        print(f'  {d[:50]:50s} -> {num} [{ok}]')

# Find missing
print(f'\nMissing from data: ')
for rn in sorted(report_nums):
    if rn not in dir_match_nums.values():
        print(f'  {rn}')

print(f'\nMissing from reports: ')
for d, num in sorted(dir_match_nums.items()):
    if num not in report_nums:
        print(f'  {num}: {d[:50]}')
