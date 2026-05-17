# -*- coding: utf-8 -*-
"""找可用的球队历史数据源"""
import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

# 曼城 teamid=2465
team_name = '曼城'
team_id = '2465'

tests = [
    # trade.500.com 已知可用端点
    ('trade-odds', 'https://trade.500.com/jczq/oupeizhilv.jsp?jid=1234567'),
    ('trade-handicap', 'https://trade.500.com/jczq/rangqiupeizhi.jsp?jid=1234567'),
    ('trade-asian', 'https://trade.500.com/jczq/yazhibijiao.jsp?jid=1234567'),
    
    # trade.500.com 球队相关可能路径
    ('trade-team1', 'https://trade.500.com/jczq/teamodds.php?teamid=2465'),
    ('trade-team2', 'https://trade.500.com/jczq/team_history.php?teamid=2465'),
    ('trade-team3', 'https://trade.500.com/jczq/team_odds.php?teamid=2465'),
    
    # liansai.500.com (这是能工作的)
    ('liansai-get', 'https://liansai.500.com/jczsear.php?p=1&type=1&keyword=%E7%94%B2&action=list'),
]

for name, url in tests:
    try:
        r = sess.get(url, timeout=15)
        snippet = r.text[:200].replace('\n', ' ')
        print('{} -> {} ({} bytes) | {}'.format(name, r.status_code, len(r.text), snippet[:120]))
    except Exception as e:
        print('{} -> ERROR: {}'.format(name, str(e)[:100]))
