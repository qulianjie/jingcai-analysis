import os, json, re

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-16'
DATA_DIR = os.path.join(TASKS_DIR, 'data')

# Load all match data
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

# Build map from match number -> data dir
dir_nums = {}
for d in os.listdir(DATA_DIR):
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
            dir_nums[num] = d

# Check each match number
print('Match coverage:')
all_nums = sorted(match_map.keys())
for num in all_nums:
    if num in dir_nums:
        d = dir_nums[num]
        dp = os.path.join(DATA_DIR, d)
        s8 = os.path.getsize(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian', 'step8_same_league.txt')) else 0
        s9 = os.path.getsize(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA', 'step9_home_history.txt')) else 0
        s14 = os.path.getsize(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB', 'step14_away_history.txt')) else 0
        s19 = os.path.getsize(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia', 'step19_baijia_compare.txt')) else 0
        s24 = os.path.exists(os.path.join(dp, 'step24_panlu_match.json'))
        ok = 'OK' if (s8 > 0 and s9 > 0 and s14 > 0 and s19 > 0 and s24) else 'INCOMPLETE'
        print(f'  {num}: {d[:50]:50s} -> {ok}')
    else:
        m = match_map[num]
        print(f'  {num}: MISSING ({m.get("home","")} vs {m.get("away","")})')
