import json, os

CACHE_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache'

# 已富集的联赛里找一个 sample
for fname in os.listdir(CACHE_DIR):
    if not fname.endswith('.json'): continue
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    if d.get('enriched'):
        ms = d.get('all_matches', [])
        for m in ms:
            if m.get('odds_europe'):
                print(f'=== 联赛: {d.get("league","?")} ({fname}) ===')
                print(f'比赛: {m.get("HOMETEAMSXNAME","")} vs {m.get("AWAYTEAMSXNAME","")} | {m.get("MATCHDATE","")} | FID={m.get("FIXTUREID","")}')
                print()
                
                # 完整打印所有根字段
                print('--- 基本字段 ---')
                for k in ['WIN','DRAW','LOST','HANDICAPLINE','HANDICAPLINENAME','HOMEMONEYLINE','AWAYMONEYLINE','BIGMONEYLINE','SMALLMONEYLINE','HOMESCORE','AWAYSCORE']:
                    print(f'  {k}: {m.get(k, "N/A")}')
                print(f'  _computed: {m.get("_computed","N/A")}')
                
                # odds_europe
                print('\n--- odds_europe ---')
                oe = m.get('odds_europe', {})
                for k, v in sorted(oe.items()):
                    if isinstance(v, dict):
                        print(f'  {k}:')
                        for k2, v2 in sorted(v.items()):
                            print(f'    {k2}: {v2}')
                    elif isinstance(v, list):
                        print(f'  {k}: [{len(v)} items]')
                        for i, item in enumerate(v[:2]):
                            print(f'    [{i}] name={item.get("name","")} init={item.get("init","")} live={item.get("live","")} dir={item.get("dir","")}')
                    else:
                        print(f'  {k}: {v}')
                
                # odds_handicap
                print('\n--- odds_handicap ---')
                oh = m.get('odds_handicap', {})
                if oh:
                    for k, v in sorted(oh.items()):
                        if isinstance(v, dict):
                            print(f'  {k}:')
                            for k2, v2 in sorted(v.items()):
                                print(f'    {k2}: {v2}')
                        else:
                            print(f'  {k}: {v}')
                
                # odds_asian
                print('\n--- odds_asian ---')
                oa = m.get('odds_asian', [])
                if oa:
                    print(f'  [{len(oa)} 家公司]')
                    for item in oa[:3]:
                        for k, v in sorted(item.items()):
                            print(f'    {k}: {v}')
                        print('  ---')
                break
        break

# 统计整体富集情况
print('\n\n======= 全局富集统计 =======')
total = 0
enriched = 0
with_oe = 0
with_oh = 0
with_oa = 0
with_score = 0
non_enriched_leagues = []
for fname in sorted(os.listdir(CACHE_DIR)):
    if not fname.endswith('.json'): continue
    total += 1
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    if d.get('enriched'):
        enriched += 1
    else:
        non_enriched_leagues.append(fname.replace('.json',''))
    ms = d.get('all_matches', [])
    for m in ms:
        e = m.get('odds_europe')
        if e and e.get('jc'):
            with_oe += 1
        if m.get('odds_handicap'):
            with_oh += 1
        if m.get('odds_asian'):
            with_oa += 1
        if m.get('HOMESCORE') != '' and m.get('AWAYSCORE') != '':
            with_score += 1

print(f'总联赛缓存: {total}')
print(f'标记enriched: {enriched}')
print(f'有odds_europe(JC)的比赛: {with_oe}')
print(f'有odds_handicap的比赛: {with_oh}')
print(f'有odds_asian的比赛: {with_oa}')
print(f'有比分的比赛: {with_score}')
print(f'未富集联赛数: {len(non_enriched_leagues)}')
if non_enriched_leagues:
    print(f'未富集联赛列表(前20):')
    for name in non_enriched_leagues[:20]:
        print(f'  {name}')
