import os, json, re

TASKS_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Check all report files
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and not f.startswith('summary')]
print(f'报告文件: {len(reports)} 份')
for r in sorted(reports):
    size = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {r[:60]:60s} {size}B')

# Check all data dirs
dirs = sorted([d for d in os.listdir(DATA_DIR) if d.startswith('match') and os.path.isdir(os.path.join(DATA_DIR, d))])
print(f'\n数据目录: {len(dirs)} 个')

# Load matches
with open(os.path.join(TASKS_DIR, 'matches_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
all_matches = []
for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        all_matches.extend(gd['matches'])
total = len(all_matches)
print(f'总比赛数: {total}')

# Find missing
dir_nums = set()
for d in dirs:
    parts = d.split('_', 1)
    num = int(parts[0].replace('match', ''))
    dir_nums.add(num)
print(f'数据目录编号: {sorted(dir_nums)}')
