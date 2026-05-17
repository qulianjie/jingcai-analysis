# -*- coding: utf-8 -*-
"""找可用的球队历史数据源"""
import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

# 曼城 teamid=2465 测试
team_name = '曼城'
team_id = '2465'

urls = [
    # zqwelc.500.com (亚盘常见源)
    ('zqwelc-1', 'https://zqwelc.500.com/zqTeamAllH2HJb.php?id=2465&leagueid=&datebegin=2026-04-01&dateend=2026-05-15'),
    # zqdata.500.com
    ('zqdata', 'https://zqdata.500.com/'),
    # zq.500.com 球队页面
    ('zq-team', 'https://zq.500.com/team/?teamid=2465'),
    # 500.com 赔率中心 - 联赛筛选
    ('pl-leagues', 'https://odds.500.com/jczq/info/jczqsqch.htm'),
    # liansai 用 POST
    ('liansai-post', 'https://liansai.500.com/jczsear.php'),
    # 500.com 球队详情
    ('500-team1', 'https://info.500.com/jczq/jczqTeamInfo.aspx?lid=22'),
    ('500-team2', 'https://zq.500.com/team/#teamid=2465'),
]

for name, url in urls:
    try:
        if name == 'liansai-post':
            data = {
                'p': '1', 'type': '1', 'keyword': team_name,
                'date': '2026-04-01', 'date2': '2026-05-15',
                'league': '', 'action': 'list',
            }
            r = sess.post(url, data=data, timeout=15)
        else:
            r = sess.get(url, timeout=15)
        has_table = 'table' in r.text.lower()
        snippet = r.text[:300].replace('\n', ' ')
        print('{} -> {} ({} bytes) table={} | {}'.format(
            name, r.status_code, len(r.text), has_table, snippet[:120]))
    except Exception as e:
        print('{} -> ERROR: {}'.format(name, str(e)[:100]))
