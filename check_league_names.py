# -*- coding: utf-8 -*-
"""Test: fetch team fixture and check league names"""
import requests, json, re
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# Fetch 水戸蜀葵 (home_id=4127) fixture
url = 'https://liansai.500.com/team/4127/teamfixture/'
try:
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    leagues_seen = set()
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            data = json.loads(tr.get('data', '{}'))
            league = data.get('SIMPLEGBNAME', '')
            if league:
                leagues_seen.add(league)
        except:
            continue
    
    print(f'Leagues seen for 水戸蜀葵: {leagues_seen}')
except Exception as e:
    print(f'Error: {e}')

# Also check 浦和红钻 (home_id=495)
url2 = 'https://liansai.500.com/team/495/teamfixture/'
try:
    resp2 = sess.get(url2, timeout=15)
    resp2.encoding = 'gbk'
    soup2 = BeautifulSoup(resp2.text, 'html.parser')
    
    leagues_seen2 = set()
    for tr in soup2.find_all('tr', attrs={'data': True}):
        try:
            data = json.loads(tr.get('data', '{}'))
            league = data.get('SIMPLEGBNAME', '')
            if league:
                leagues_seen2.add(league)
        except:
            continue
    
    print(f'Leagues seen for 浦和红钻: {leagues_seen2}')
except Exception as e:
    print(f'Error: {e}')

# Check 弗赖堡 (home_id=804)
url3 = 'https://liansai.500.com/team/804/teamfixture/'
try:
    resp3 = sess.get(url3, timeout=15)
    resp3.encoding = 'gbk'
    soup3 = BeautifulSoup(resp3.text, 'html.parser')
    
    leagues_seen3 = set()
    for tr in soup3.find_all('tr', attrs={'data': True}):
        try:
            data = json.loads(tr.get('data', '{}'))
            league = data.get('SIMPLEGBNAME', '')
            if league:
                leagues_seen3.add(league)
        except:
            continue
    
    print(f'Leagues seen for 弗赖堡: {leagues_seen3}')
except Exception as e:
    print(f'Error: {e}')
