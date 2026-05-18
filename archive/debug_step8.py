# -*- coding: utf-8 -*-
"""Debug step8 for match4 fid=1411377 - find correct directory"""
import glob, json, os, sys, re, requests
from bs4 import BeautifulSoup

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 找到所有 match4 目录
all_match4 = glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match4*'))
print(f"找到 {len(all_match4)} 个 match4 目录:")

target_dir = None
for d in all_match4:
    meta_path = os.path.join(d, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        fid = meta.get('fid', '')
        league = meta.get('league', '')
        print(f"  {d}")
        print(f"    fid={fid}, league={repr(league)}, macau_line={repr(meta.get('macau_line'))}")
        if fid == '1411377':
            target_dir = d

if not target_dir:
    print("ERROR: 找不到 fid=1411377")
    sys.exit(1)

print(f"\n目标目录: {target_dir}")

meta_path = os.path.join(target_dir, 'meta.json')
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

LEAGUE = meta.get('league', '')
HOME_ID = meta.get('home_id', '')
MACAU_LINE = meta.get('macau_line', '')

print(f"联赛: {repr(LEAGUE)}")
print(f"主队ID: {HOME_ID}")
print(f"澳门盘口: {repr(MACAU_LINE)}")

# 获取联赛ID
sys.path.insert(0, base)
from step8_1923_extractor import _build_league_id_map, _league_match, _handicap_match
LEAGUE_ID_MAP = _build_league_id_map()
league_id = LEAGUE_ID_MAP.get(LEAGUE, '')
print(f"联赛ID: {league_id}")

# 获取联赛球队
sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

team_ids = set()
if league_id:
    league_url = f'https://liansai.500.com/zuqiu-{league_id}/'
    try:
        resp = sess.get(league_url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)', href)
            if m and '/teamfixture/' not in href:
                team_ids.add(m.group(1))
    except Exception as e:
        print(f"获取联赛球队失败: {e}")

print(f"联赛球队数: {len(team_ids)}")

# 获取所有球队赛程
all_matches = []
for team_id in sorted(team_ids)[:5]:  # 只取前5支球队
    url = f'https://liansai.500.com/team/{team_id}/teamfixture/'
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                all_matches.append(data)
            except:
                continue
    except:
        pass

print(f"总记录数: {len(all_matches)}")

# 检查联赛名匹配
print()
print("=== 联赛名匹配检查 ===")
src_leagues = set()
for d in all_matches:
    src_league = d.get('SIMPLEGBNAME', '')
    if src_league:
        src_leagues.add(src_league)

print(f"源站联赛名 (前20个):")
for sl in sorted(src_leagues)[:20]:
    match = _league_match(sl, LEAGUE)
    print(f"  {repr(sl)} -> match={match}")

# 筛选相同联赛
league_matches = []
seen_fid = set()
for d in all_matches:
    if not _league_match(d.get('SIMPLEGBNAME',''), LEAGUE): continue
    if d.get('FIXTUREID','') in seen_fid: continue
    seen_fid.add(d.get('FIXTUREID',''))
    league_matches.append(d)

print(f"\n同联赛筛选: {len(league_matches)} 场")

# 检查盘口匹配
if league_matches:
    print()
    print("=== 盘口匹配检查 (前10场) ===")
    for d in league_matches[:10]:
        hcp = d.get('HANDICAPLINENAME', '')
        match = False
        if MACAU_LINE and hcp:
            match = _handicap_match(MACAU_LINE, hcp)
        print(f"  {d.get('MATCHDATE','')} | {d.get('HOMETEAMSXNAME','')} vs {d.get('AWAYTEAMSXNAME','')} | 盘口={repr(hcp)} | match={match}")
