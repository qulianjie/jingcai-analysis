import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'

with open(matches_file, 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

if isinstance(matches_data, dict) and 'groups' in matches_data:
    all_matches = []
    for gn, gd in matches_data['groups'].items():
        if isinstance(gd, dict) and 'matches' in gd:
            all_matches.extend(gd['matches'])
    matches_list = all_matches
elif isinstance(matches_data, list):
    matches_list = matches_data
elif isinstance(matches_data, dict) and 'matches' in matches_data:
    matches_list = matches_data['matches']
else:
    matches_list = []

match_map = {}
for m in matches_list:
    num = m.get('matchnum', '')
    if num:
        match_map[num] = m

dirs = sorted([d for d in os.listdir(base) if d.startswith('match') and os.path.isdir(os.path.join(base, d))])

for d in dirs:
    dp = os.path.join(base, d)
    meta_path = os.path.join(dp, 'meta.json')
    
    # Check if meta needs fixing
    needs_fix = False
    if not os.path.exists(meta_path):
        needs_fix = True
    else:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if not meta.get('league') or not meta.get('home_id'):
            needs_fix = True
    
    if not needs_fix:
        continue
    
    # Extract match number from dir name
    parts = d.split('_', 1)
    if len(parts) < 2:
        continue
    match_num_raw = parts[0].replace('match', '')
    match_num_padded = f"{int(match_num_raw):03d}"
    
    match_info = match_map.get(match_num_padded) or match_map.get(match_num_raw)
    if not match_info:
        print(f'WARN {d}: no match data for {match_num_padded}')
        continue
    
    meta = {
        'matchnum': match_info.get('matchnum', match_num_padded),
        'match': '{} {} vs {}'.format(match_info.get('matchnum', match_num_padded), match_info.get('home',''), match_info.get('away','')),
        'fid': match_info.get('fid', ''),
        'league': match_info.get('league', ''),
        'home': match_info.get('home', ''),
        'away': match_info.get('away', ''),
        'date': '2026-05-16',
        'status': 'in_progress',
        'home_id': match_info.get('home_id', ''),
        'away_id': match_info.get('away_id', ''),
        'rq': match_info.get('rq', ''),
        'macau_line': match_info.get('macau_line', ''),
    }
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f'FIXED {d}: league={meta["league"]} home_id={meta["home_id"]} away_id={meta["away_id"]} fid={meta["fid"]} macau={meta["macau_line"]}')
