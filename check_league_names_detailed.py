# -*- coding: utf-8 -*-
"""Check actual SIMPLEGBNAME values for all leagues"""
import requests, json, re, sys
from bs4 import BeautifulSoup
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def check_league_teams(league_id, league_name, known_teams=[]):
    """Check what SIMPLEGBNAME the extracted teams have"""
    # Get teams from league page
    url = f'https://liansai.500.com/zuqiu-{league_id}/'
    try:
        r = sess.get(url, timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        team_ids = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)', href)
            if m and '/teamfixture/' not in href:
                team_ids.add(m.group(1))
    except:
        team_ids = set(known_teams)
    
    if not team_ids and known_teams:
        team_ids = set(known_teams)
    
    print(f"\n=== {league_name} (ID={league_id}) ===")
    print(f"提取球队: {list(team_ids)[:5]}... ({len(team_ids)} total)")
    
    all_names = set()
    for i, tid in enumerate(list(team_ids)[:5]):
        url = f'https://liansai.500.com/team/{tid}/teamfixture/'
        try:
            r = sess.get(url, timeout=15)
            r.encoding = 'gbk'
            soup = BeautifulSoup(r.text, 'html.parser')
            names = set()
            for tr in soup.find_all('tr', attrs={'data': True}):
                try:
                    d = json.loads(tr.get('data', '{}'))
                    names.add(d.get('SIMPLEGBNAME', ''))
                except: pass
            all_names.update(names)
            print(f"  {tid}: {names}")
            if i < 4:
                import time
                time.sleep(0.2)
        except:
            print(f"  {tid}: ERROR")
    
    print(f"所有SIMPLEGBNAME: {all_names}")
    return all_names

# Check欧冠
ucl_names = check_league_teams('19538', '欧冠')

# Check解放者杯
lib_names = check_league_teams('19546', '解放者杯')

# Check沙特
sau_names = check_league_teams('19506', '沙特')

# Check芬超
fin_names = check_league_teams('19510', '芬超')

# Check荷乙
ned_names = check_league_teams('19502', '荷乙')

print("\n=== League match check ===")
target_names = {'欧冠': ucl_names, '解放者杯': lib_names, '沙特': sau_names, '芬超': fin_names, '荷乙': ned_names}
for target, names in target_names.items():
    for n in names:
        if target == n:
            print(f"  {target}: EXACT MATCH with '{n}'")
        elif target in n or n in target:
            print(f"  {target}: SUBSTRING MATCH with '{n}'")
