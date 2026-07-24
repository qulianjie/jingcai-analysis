import json, os

CACHE_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache'
files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
print(f'共 {len(files)} 个联赛缓存文件')

# Sample 世界杯
with open(os.path.join(CACHE_DIR, '世界杯.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
print('\n=== 世界杯 ===')
print('Keys:', list(data.keys()))
print('League:', data.get('league','?'))
all_m = data.get('all_matches',[])
print(f'比赛数量: {len(all_m)}')

if all_m:
    # Show match fields
    m = all_m[200] if len(all_m) > 200 else all_m[0]
    print('\n--- 字段 (非dict非list) ---')
    for k,v in sorted(m.items()):
        if not isinstance(v, (dict, list)):
            print(f'  {k}: {v}')
    print()
    for k,v in sorted(m.items()):
        if isinstance(v, (dict, list)):
            print(f'  {k}: {type(v).__name__}', end='')
            if isinstance(v, dict):
                print(f' keys={list(v.keys())[:5]}')
            else:
                print(f' len={len(v)}')
    
    # Check enriched status
    print(f'\n富集状态: enriched={data.get("enriched")}')
    print(f'富集日期: {data.get("enriched_date")}')
    enriched_count = sum(1 for m2 in all_m if m2.get('odds_europe'))
    print(f'有odds数据: {enriched_count}/{len(all_m)}')

    # Date range
    dates = [m2.get('MATCHDATE','') for m2 in all_m if m2.get('MATCHDATE')]
    if dates:
        print(f'日期范围: {min(dates)} ~ {max(dates)}')
    
    # How many have actual scores
    with_score = sum(1 for m2 in all_m if m2.get('HOMESCORE') != '' and m2.get('AWAYSCORE') != '')
    print(f'有比分: {with_score}/{len(all_m)}')
    
    # Available info
    handicap = sum(1 for m2 in all_m if m2.get('HANDICAPLINE') is not None and m2.get('HANDICAPLINE') != '')
    print(f'有让球: {handicap}/{len(all_m)}')

# Check how many leagues are enriched vs not
enriched_leagues = 0
total_matches = 0
for fname in files:
    with open(os.path.join(CACHE_DIR, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)
    matches = d.get('all_matches', [])
    total_matches += len(matches)
    if d.get('enriched'):
        enriched_leagues += 1
        
print(f'\n=== 全局统计 ===')
print(f'总缓存文件: {len(files)}')
print(f'已富集: {enriched_leagues}')
print(f'总比赛场次: {total_matches}')

# Now check what training_data.json actually looks like
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\training_data.json', 'r', encoding='utf-8') as f:
    td = json.load(f)
print(f'\n=== 当前训练集 ===')
print(f'版本: {td.get("version")}')
print(f'总数: {td.get("total")}')
samples = td.get('samples', [])
dim_counts = {}
for s in samples:
    ds = s.get('dim_scores', {})
    for d in ds:
        dim_counts[d] = dim_counts.get(d, 0) + 1
print(f'\n维度覆盖率({len(samples)}条):')
for d, c in sorted(dim_counts.items(), key=lambda x:-x[1]):
    print(f'  {d}: {c}/{len(samples)} ({c/len(samples)*100:.0f}%)')
print(f'\n赛果分布:')
actual_dist = {}
for s in samples:
    a = s.get('actual','?')
    actual_dist[a] = actual_dist.get(a, 0) + 1
for k in ['胜','平','负']:
    print(f'  {k}: {actual_dist.get(k,0)} ({actual_dist.get(k,0)/len(samples)*100:.1f}%)')
