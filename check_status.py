import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted([d for d in os.listdir(base) if d.startswith('match') and os.path.isdir(os.path.join(base, d))])

print(f'Total dirs: {len(dirs)}')
print()

missing = 0
ok = 0
for d in dirs:
    dp = os.path.join(base, d)
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian/step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) else 0
    
    ok_flag = s8 > 500 and s9 > 500 and s14 > 500 and s19 > 500
    if ok_flag:
        ok += 1
    else:
        missing += 1
    
    # Read meta for display
    meta_path = os.path.join(dp, 'meta.json')
    league = ''
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            m = json.load(f)
        league = m.get('league', '')
    
    tag = 'OK' if ok_flag else 'MISS'
    print(f'  {tag} {d}: s8={s8}B s9={s9}B s14={s14}B s19={s19}B league={league}')

print(f'\nOK: {ok}, Missing: {missing}')
