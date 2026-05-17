import os, sys, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
dirs = sorted([d for d in os.listdir(base) if d.startswith('match')])

print('当前所有比赛状态:')
print()
ok = 0
miss = 0
missing_list = []

for d in dirs:
    dp = os.path.join(base, d)
    meta_path = os.path.join(dp, 'meta.json')
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    s8 = os.path.getsize(os.path.join(dp, 'group03_asian/step8_same_league.txt')) if os.path.exists(os.path.join(dp, 'group03_asian/step8_same_league.txt')) else 0
    s9 = os.path.getsize(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) if os.path.exists(os.path.join(dp, 'group04_teamA/step9_home_history.txt')) else 0
    s14 = os.path.getsize(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) if os.path.exists(os.path.join(dp, 'group05_teamB/step14_away_history.txt')) else 0
    s19 = os.path.getsize(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) if os.path.exists(os.path.join(dp, 'group06_baijia/step19_baijia_compare.txt')) else 0
    
    ok_flag = s8 > 500 and s9 > 500 and s14 > 500 and s19 > 500
    tag = 'OK' if ok_flag else 'MISS'
    if ok_flag: ok += 1
    else:
        miss += 1
        missing_list.append(d)
    
    print(f'  {tag} {meta.get("matchnum","?")}: {d} -> s8={s8}B s9={s9}B s14={s14}B s19={s19}B')

print(f'\n总计: OK={ok}, Missing={miss}')
print(f'\n缺失的目录: {missing_list}')
