import json

TARGET_HANDICAP = -1.25
WIN_MIN = 1.30
WIN_MAX = 1.39

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache\芬超.json', encoding='utf-8') as f:
    data = json.load(f)

all_m = data.get('all_matches', [])
c = 0
for m in all_m:
    if not isinstance(m, dict):
        continue
    try:
        hc = float(m.get('HANDICAPLINE') or 0)
    except:
        continue
    if hc != TARGET_HANDICAP:
        continue
    try:
        w = float(m.get('WIN') or 0)
    except:
        continue
    if WIN_MIN <= w <= WIN_MAX:
        c += 1
        print(f"{m.get('MATCHDATE','')} | {m.get('HOMETEAMSXNAME','')} vs {m.get('AWAYTEAMSXNAME','')} | {w} / {m.get('DRAW','')} / {m.get('LOST','')} | {m.get('HANDICAPLINENAME','')} | {m.get('HOMESCORE','?')}:{m.get('AWAYSCORE','?')}")

print(f'{c}')
