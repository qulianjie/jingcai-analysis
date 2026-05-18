import os, json

base = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'

# Load matches
with open(matches_file, 'r', encoding='utf-8') as f:
    matches_data = json.load(f)

# Handle groups format
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

print(f'Loaded {len(matches_list)} matches')

# Build match_num -> match mapping
match_map = {}
for m in matches_list:
    num = m.get('matchnum', '')
    if num:
        match_map[num] = m

# Find dirs missing meta.json
dirs = sorted([d for d in os.listdir(base) if d.startswith('match') and os.path.isdir(os.path.join(base, d))])

fixed = 0
for d in dirs:
    meta_path = os.path.join(base, d, 'meta.json')
    if os.path.exists(meta_path):
        continue
    
    # Extract match number from dir name: match7_川崎前锋__柏太阳神
    parts = d.split('_', 1)
    if len(parts) < 2:
        print(f'SKIP {d} - cannot parse')
        continue
    
    match_num = parts[0].replace('match', '')  # e.g. "7"
    match_num_padded = f"{int(match_num):03d}"  # e.g. "007"
    
    # Find match in map
    match_info = match_map.get(match_num_padded)
    if not match_info:
        # Try without padding
        match_info = match_map.get(match_num)
    
    if not match_info:
        print(f'WARN {d} - no match found for num={match_num_padded}')
        continue
    
    # Create meta.json
    meta = {
        'matchnum': match_info.get('matchnum', match_num_padded),
        'match': f"{match_info.get('matchnum', match_num_padded)} {match_info.get('home','')} vs {match_info.get('away','')}",
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
    
    fixed += 1
    print(f'FIXED {d}: league={meta["league"]} home={meta["home"]} away={meta["away"]} home_id={meta["home_id"]} away_id={meta["away_id"]} fid={meta["fid"]} macau={meta["macau_line"]}')

print(f'\nFixed {fixed} meta.json files')
