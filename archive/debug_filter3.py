# -*- coding: utf-8 -*-
"""Debug step918 filter3"""
import sys, os, json

sys.path.insert(0, os.getcwd())
from step918_extractor import fetch_team, filter3

# Test a match that's missing g4/g5
# 5/10 match7: 忨__ (home_id=1095, away_id=1128, league=Ӣ)
meta = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data\match7_忨__\meta.json', encoding='utf-8'))
print('meta:', json.dumps(meta, ensure_ascii=False, indent=2))

home_id = meta.get('home_id', '')
away_id = meta.get('away_id', '')
league = meta.get('league', '')
macau_line = meta.get('macau_line', '')

print('\nhome_id={}, away_id={}, league={}, macau_line={}'.format(home_id, away_id, league, macau_line))

# Fetch team data
home_data = fetch_team(str(home_id))
print('\nfetch_team({}) returned {} records'.format(home_id, len(home_data)))

if home_data:
    # Show sample
    print('Sample record keys:', list(home_data[0].keys())[:10])
    print('Sample:', json.dumps(home_data[0], ensure_ascii=False)[:300])
    
    # Check league names in data
    leagues = set(d.get('SIMPLEGBNAME', '') for d in home_data)
    print('\nLeagues in home data:', sorted(leagues))
    
    # Check home team IDs
    home_ids = set(str(d.get('HOMETEAMID', '')) for d in home_data)
    print('home_id {} in data: {}'.format(home_id, str(home_id) in home_ids))
    
    # Test filter3
    filtered = filter3(home_data, str(home_id), 'home', league, macau_line)
    print('\nfilter3(home, league={}, macau_line={}) -> {} results'.format(league, macau_line, len(filtered)))
    
    # Test without macau_line filter
    filtered2 = filter3(home_data, str(home_id), 'home', league, '')
    print('filter3(home, league={}, macau_line=empty) -> {} results'.format(league, len(filtered2)))
    
    # Test without league filter (use empty league)
    filtered3 = filter3(home_data, str(home_id), 'home', '', macau_line)
    print('filter3(home, league=empty, macau_line={}) -> {} results'.format(macau_line, len(filtered3)))
else:
    print('No data returned!')
