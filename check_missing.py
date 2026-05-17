import os, json
base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted(os.listdir(base))
print('Dirs:', len(dirs))

missing_s8 = missing_s9 = missing_s14 = missing_s19 = 0
for d in dirs:
    dp = os.path.join(base, d)
    s8 = os.path.join(dp, 'group03_asian/step8_same_league.txt')
    s9 = os.path.join(dp, 'group04_teamA/step9_home_history.txt')
    s14 = os.path.join(dp, 'group05_teamB/step14_away_history.txt')
    s19 = os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')
    s1 = os.path.join(dp, 'group01_europe/step1_europe_base.txt')
    has_s1 = os.path.exists(s1)
    has_s8 = os.path.exists(s8)
    has_s9 = os.path.exists(s9)
    has_s14 = os.path.exists(s14)
    has_s19 = os.path.exists(s19)
    if not has_s8: missing_s8 += 1
    if not has_s9: missing_s9 += 1
    if not has_s14: missing_s14 += 1
    if not has_s19: missing_s19 += 1
    if not has_s8 or not has_s9 or not has_s14 or not has_s19:
        print(f'  {d}: s1={has_s1} s8={has_s8} s9={has_s9} s14={has_s14} s19={has_s19}')

print(f'\nMissing: s8={missing_s8}, s9={missing_s9}, s14={missing_s14}, s19={missing_s19}')
