import os, json

TASKS_DIR = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Count reports
reports = [f for f in os.listdir(TASKS_DIR) if f.endswith('.md') and not f.startswith('summary') and f != 'sunday_matches.md']
print(f'报告文件: {len(reports)} 份')
for r in sorted(reports):
    num = r[:6]  # e.g. 周日001
    size = os.path.getsize(os.path.join(TASKS_DIR, r))
    print(f'  {num} {size:>7}B')

# Check each new dir (match24+)
print('\n新数据目录 (match24+):')
for d in sorted(os.listdir(DATA_DIR)):
    if not d.startswith('match') or not os.path.isdir(os.path.join(DATA_DIR, d)):
        continue
    num = d.split('_')[0].replace('match', '')
    if int(num) < 24:
        continue
    
    dp = os.path.join(DATA_DIR, d)
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
    s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
    
    meta_path = os.path.join(dp, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        matchnum = meta.get('matchnum', '?')
    else:
        matchnum = '?'
    
    status = 'OK' if (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24) else 'INCOMPLETE'
    print(f'  {d[:50]:50s} {matchnum} -> s8={s8} s9={s9} s14={s14} s19={s19} s24={s24} [{status}]')
