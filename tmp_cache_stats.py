import json, os
from collections import defaultdict

CACHE_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache'

# 统计：有多少比赛能同时提供哪些特征
stats = {
    'basic_odds': 0,   # WIN/DRAW/LOST
    'handicap': 0,     # HANDICAPLINE
    'asian': 0,        # HOMEMONEYLINE + AWAYMONEYLINE
    'score': 0,        # HOMESCORE + AWAYSCORE
    'all_basic': 0,    # basic_odds + handicap + score
    'all_full': 0,     # all_basic + asian
}

league_data = []
for fname in sorted(os.listdir(CACHE_DIR)):
    if not fname.endswith('.json'): continue
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    league = d.get('league', fname.replace('.json',''))
    ms = d.get('all_matches', [])
    
    league_stats = defaultdict(int)
    for m in ms:
        has_odds = m.get('WIN') is not None
        has_hc = m.get('HANDICAPLINE') is not None and m.get('HANDICAPLINE') != ''
        has_asian = m.get('HOMEMONEYLINE') is not None and m.get('AWAYMONEYLINE') is not None
        has_score = m.get('HOMESCORE') != '' and m.get('AWAYSCORE') != ''
        
        if has_odds: stats['basic_odds'] += 1; league_stats['basic_odds'] += 1
        if has_hc: stats['handicap'] += 1; league_stats['handicap'] += 1
        if has_asian: stats['asian'] += 1; league_stats['asian'] += 1
        if has_score: stats['score'] += 1
        if has_odds and has_hc and has_score: stats['all_basic'] += 1; league_stats['all_basic'] += 1
        if has_odds and has_hc and has_asian and has_score: stats['all_full'] += 1; league_stats['all_full'] += 1
    
    if league_stats['all_basic'] > 0:
        league_data.append((league, league_stats))

print('=== 缓存数据可用性统计 ===')
print(f'总比赛数: {sum(v for v in stats.values()) // 7}')
print(f'有基本欧赔(WIN/DRAW/LOST): {stats["basic_odds"]}')
print(f'有让球线(HANDICAPLINE): {stats["handicap"]}')
print(f'有亚盘水位(HOMEMONEYLINE/AWAYMONEYLINE): {stats["asian"]}')
print(f'有比分: {stats["score"]}')
print(f'有【三价欧赔+让球+比分】: {stats["all_basic"]}')
print(f'有【全部特征+比分】: {stats["all_full"]}')

print('\n=== 按联赛看可用数据(>1000条all_basic的联赛) ===')
league_data.sort(key=lambda x: -x[1]['all_basic'])
for league, ls in league_data[:30]:
    pct = ls['all_basic'] / max(ls['basic_odds'], 1) * 100
    print(f'{league:15s} all_basic={ls["all_basic"]:>5d}  odds={ls["basic_odds"]:>5d}  hc={ls["handicap"]:>5d}  full={ls["all_full"]:>5d}  ({pct:.0f}%)')

# 赛果分布 - 取样看match_result分类
result_dist = defaultdict(int)
league_checked = 0
for fname in os.listdir(CACHE_DIR):
    if not fname.endswith('.json'): continue
    league_checked += 1
    if league_checked > 100: break
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    for m in d.get('all_matches', []):
        c = m.get('_computed', {})
        if c and c.get('match_result'):
            result_dist[c['match_result']] += 1

print(f'\n=== 赛果分布(抽100个联赛) ===')
total = sum(result_dist.values())
for k in ['主胜','平局','客胜']:
    print(f'{k}: {result_dist.get(k,0)} ({result_dist.get(k,0)/total*100:.1f}%)')
