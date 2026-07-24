import json, os

CACHE_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache'

# 深入分析："已富集但空的"占多少
total_matches = 0
enriched_flag_true = 0
enriched_flag_false = 0
has_odds_jc = 0
has_odds_company = 0  # 有至少一家公司数据
has_handicap = 0
has_asian = 0
has_basic_odds = 0  # 有WIN/DRAW/LOST基本欧赔
dead_fids = 0

league_stats = []

for fname in sorted(os.listdir(CACHE_DIR)):
    if not fname.endswith('.json'): continue
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    league = d.get('league', fname)
    ms = d.get('all_matches', [])
    total_matches += len(ms)
    
    if d.get('enriched'):
        enriched_flag_true += 1
    else:
        enriched_flag_false += 1
    
    league_has_odds = 0
    league_has_basic = 0
    league_empty_enriched = 0
    league_with_score = 0
    
    for m in ms:
        # Basic odds present?
        if m.get('WIN') is not None:
            has_basic_odds += 1
            league_has_basic += 1
        
        # Has actual odds_europe data?
        oe = m.get('odds_europe', {})
        if isinstance(oe, dict) and oe.get('jc') and oe['jc'].get('iw'):
            has_odds_jc += 1
            league_has_odds += 1
        elif d.get('enriched'):
            # Enriched but no JC data
            league_empty_enriched += 1
        
        if m.get('odds_handicap'):
            has_handicap += 1
        if m.get('odds_asian'):
            has_asian += 1
        
        if m.get('HOMESCORE') != '' and m.get('AWAYSCORE') != '':
            league_with_score += 1
    
    league_stats.append({
        'name': league,
        'total': len(ms),
        'has_odds': league_has_odds,
        'has_basic': league_has_basic,
        'empty': league_empty_enriched,
        'enriched': d.get('enriched', False),
        'with_score': league_with_score,
    })

print(f'总比赛: {total_matches}')
print(f'  有WIN/DRAW/LOST基本欧赔: {has_basic_odds}')
print(f'  有odds_europe(JC)数据: {has_odds_jc}')
print(f'  有亚盘水位: {has_asian}')
print(f'  有让球赔率: {has_handicap}')
print(f'  有比分: 295626')

print(f'\n联赛等级: {enriched_flag_true} 已富集, {enriched_flag_false} 未富集')

# 看"空富集"最严重的联赛
print('\n=== 空富集最严重的联赛（标记enriched但实际有odds数据极少）===')
empty_leagues = [s for s in league_stats if s['enriched'] and s['total'] > 0]
empty_leagues.sort(key=lambda x: x['empty'] / max(x['total'], 1), reverse=True)
for s in empty_leagues[:15]:
    print(f'  {s["name"]}: {s["total"]}场, 有odds={s["has_odds"]}, 空富集={s["empty"]} ({s["empty"]/s["total"]*100:.0f}%), 有比分={s["with_score"]}')

# 看真正有用的联赛
print('\n=== 有odds数据最多的联赛 ===')
good_leagues = [s for s in league_stats if s['has_odds'] > 0]
good_leagues.sort(key=lambda x: -x['has_odds'])
for s in good_leagues[:15]:
    print(f'  {s["name"]}: {s["has_odds"]}/{s["total"]}场有odds, 有比分={s["with_score"]}')

# 基本欧赔(WIN/DRAW/LOST)覆盖
print('\n=== 基本欧赔WIN/DRAW/LOST覆盖 ===')
basic_leagues = [s for s in league_stats if s['has_basic'] > 0]
basic_leagues.sort(key=lambda x: -x['has_basic'])
total_basic = sum(s['has_basic'] for s in basic_leagues)
print(f'总共有win/draw/lost数据的比赛: {total_basic}')
print(f'覆盖的联赛数: {len(basic_leagues)}')

# Check why世界杯 is not enriched
print('\n=== 世界杯（未富集）===')
for s in league_stats:
    if '世界杯' in s['name']:
        print(f'  {s["name"]}: {s["total"]}场, enriched={s["enriched"]}, has_odds={s["has_odds"]}, has_basic={s["has_basic"]}, with_score={s["with_score"]}')
