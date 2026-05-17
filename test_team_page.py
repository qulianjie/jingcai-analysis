# -*- coding: utf-8 -*-
"""测试 trade.500.com teamoddschange 页面"""
import requests
from bs4 import BeautifulSoup

url = 'https://trade.500.com/jczq/teamoddschange.php?teamid=15541&page=1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'gbk'
soup = BeautifulSoup(r.text, 'html.parser')

table = soup.find('table')
print('Table found:', table is not None)

if table:
    rows = table.find_all('tr')
    print('Rows:', len(rows))
    if len(rows) > 0:
        print('First row:')
        print(rows[0].prettify()[:500])
else:
    print('No table found, printing HTML snippet:')
    print(r.text[:2000])
