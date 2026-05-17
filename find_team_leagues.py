# -*- coding: utf-8 -*-
"""Find correct league IDs by checking team fixture pages"""
import requests, json, re, sys, time
from bs4 import BeautifulSoup
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Teams from meta.json for each match
teams_to_check = {
    '阿森纳': '554',
    '马竞': '1046',
    '赫尔辛基': '363',  # 芬超
    '国际图尔': '366',
    '瓦尔韦克': '5844',
    '威廉二世': '5860',
    '赛哈特海湾': '',
    '利雅得新月': '380',
    '水晶体育': '',
    '帕梅拉斯': '2640',
}

for team_name, team_id in teams_to_check.items():
    if not team_id:
        continue
    url = f'https://liansai.500.com/team/{team_id}/teamfixture/'
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
        print(f"{team_name} (ID={team_id}): {names}")
        time.sleep(0.2)
    except Exception as e:
        print(f"{team_name} (ID={team_id}): ERROR - {e}")
