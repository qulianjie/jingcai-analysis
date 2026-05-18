# -*- coding: utf-8 -*-
"""Fix missing home_id/away_id in meta.json files"""
import json, os, requests, time
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

DATA_DIR = r'jingcai\tasks\2026-05-05\data'

# Known team IDs (from 500.com)
KNOWN_TEAMS = {
    '瓦尔韦克': '5844', '威廉二世': '5860',
    '赛哈特海湾': '4027', '利雅得新月': '380',
    '阿森纳': '554', '马竞': '1046',
    '水晶体育': '8167', '帕梅拉斯': '2640',
    '圣彼得堡泽尼特': '2687', '亚特兰大': '1327',
    '江原FC': '5739', '浦项制铁': '1608',
    '首尔FC': '1606', '安养FC': '4544',
    '赫尔辛基火花': '363', '国际图尔': '366',
    '全北现代': '1609', '光州FC': '6477',
    '水原FC': '5823', '帕尔梅拉斯': '2640',
}

# Also search by team name on 500.com
def search_team_id(team_name):
    """Search for team ID on 500.com"""
    try:
        url = f'https://so.500.com/search?keyword={team_name}&type=team'
        r = sess.get(url, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if '/team/' in href and team_name in a.get_text():
                import re
                m = re.search(r'/team/(\d+)', href)
                if m:
                    return m.group(1)
    except: pass
    return None

for d in sorted(os.listdir(DATA_DIR)):
    match_dir = os.path.join(DATA_DIR, d)
    if not os.path.isdir(match_dir): continue
    meta_file = os.path.join(match_dir, 'meta.json')
    if not os.path.isfile(meta_file): continue
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    home = meta.get('home', '')
    away = meta.get('away', '')
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    
    changed = False
    
    if not home_id and home:
        # Try known teams first
        if home in KNOWN_TEAMS:
            home_id = KNOWN_TEAMS[home]
            print(f"  {home} -> {home_id} (known)")
        else:
            # Search
            hid = search_team_id(home)
            if hid:
                home_id = hid
                print(f"  {home} -> {home_id} (searched)")
            else:
                print(f"  ⚠️ {home}: 未找到")
        meta['home_id'] = home_id
        changed = True
    
    if not away_id and away:
        if away in KNOWN_TEAMS:
            away_id = KNOWN_TEAMS[away]
            print(f"  {away} -> {away_id} (known)")
        else:
            aid = search_team_id(away)
            if aid:
                away_id = aid
                print(f"  {away} -> {away_id} (searched)")
            else:
                print(f"  ⚠️ {away}: 未找到")
        meta['away_id'] = away_id
        changed = True
    
    if changed:
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"✅ Updated: {meta.get('matchnum', '')} {home}vs{away} home_id={home_id} away_id={away_id}")
    
    time.sleep(0.1)

print("\n全部完成！")
