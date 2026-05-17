# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import json

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Test liansai.500.com/team/{id}/teamfixture/
url = 'https://liansai.500.com/team/2465/teamfixture/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

trs = soup.find_all('tr', attrs={'data': True})
print('trs found:', len(trs))
if trs:
    data = json.loads(trs[0].get('data', '{}'))
    print('First record:', json.dumps(data, ensure_ascii=False)[:300])
