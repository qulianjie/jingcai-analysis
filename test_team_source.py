# -*- coding: utf-8 -*-
"""测试球队数据源"""
import requests
from bs4 import BeautifulSoup
import urllib.parse

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

# 测试不同数据源
tests = [
    # trade.500.com 变体
    ('trade-v1', 'https://trade.500.com/jczq/teamoddschange.php?teamid=2465&page=1'),
    ('trade-v2', 'https://trade.500.com/jczq/teams_oddschange.php?teamid=2465&page=1'),
    
    # liansai.500.com 搜索
    ('liansai-search', 'https://liansai.500.com/jczsear.php?type=1&keyword=曼城&action=list'),
    
    # 500.com 赔率搜索
    ('500-pl', 'https://odds.500.com/jczq/info/jczqsqch.htm'),
    ('500-pl2', 'https://info.500.com.cn/jczq/'),
]

for name, url in tests:
    try:
        r = sess.get(url, timeout=15)
        snippet = r.text[:300].replace('\n', ' ')
        print('{} -> {} ({} bytes) {}'.format(name, r.status_code, len(r.text), snippet[:150]))
    except Exception as e:
        print('{} -> ERROR: {}'.format(name, e))
