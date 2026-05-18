# -*- coding: utf-8 -*-
"""测试 step918 对具体球队的处理"""
import sys, os, json

sys.path.insert(0, os.getcwd())
from step918_extractor import fetch_team, filter3, _league_match

# 从之前的检查结果中获取缺失的 match
test_cases = [
    ('2026-05-08', 'match12', '985', '622', 'Ӣ'),
    ('2026-05-12', 'match5', '673', '564', 'Ӣ'),
    ('2026-05-12', 'match6', '6597', '2155', 'Ӣ'),
    ('2026-05-12', 'match7', '1128', '1095', 'Ӣ'),
    ('2026-05-12', 'match8', '622', '1046', 'Ӣ'),
    ('2026-05-13', 'match5', '1593', '1194', 'Ӣ'),
    ('2026-05-13', 'match6', '1072', '516', 'Ӣ'),
    ('2026-05-13', 'match7', '964', '846', ''),
]

# 先测试一个能正常处理的 match
good_cases = [
    ('2026-05-11', 'match1', '15541', '2320'),
]

for date, match, home_id, away_id, league in test_cases[:3]:
    print('\n=== {} {} (league={}) ==='.format(date, match, league))
    home_id_str = str(home_id)
    
    data = fetch_team(home_id_str)
    print('  fetch_team({}) returned {} records'.format(home_id_str, len(data)))
    
    if data:
        sample = data[0]
        print('  Sample keys:', list(sample.keys())[:10])
        print('  Sample: HOMETEAMID={} AWAYTEAMID={} SIMPLEGBNAME={}'.format(
            sample.get('HOMETEAMID'), sample.get('AWAYTEAMID'), sample.get('SIMPLEGBNAME')))
        
        # Test filter3 with empty macau_line
        filtered = filter3(data, home_id_str, 'home', league, '')
        print('  filter3(home, league={}, macau_line=empty) -> {} results'.format(league, len(filtered)))
        
        # Check league names
        league_names = set(d.get('SIMPLEGBNAME', '') for d in data)
        print('  Available leagues in data:', sorted(league_names))
        
        # Check team IDs
        home_ids = set(d.get('HOMETEAMID', '') for d in data)
        print('  home_id in data:', home_id_str, '->', home_id_str in [str(x) for x in home_ids])
    else:
        print('  No data returned')
