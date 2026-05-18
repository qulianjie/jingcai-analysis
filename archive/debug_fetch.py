# -*- coding: utf-8 -*-
import requests
import re

url = 'https://trade.500.com/jczq/?playid=271&g=2&date=2026-04-03'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.headers.update(headers)
session.get('https://trade.500.com/', timeout=10)
resp = session.get(url, timeout=15)
html = resp.content.decode('gbk', errors='ignore')

print('Length:', len(html))

# Check for tr blocks
tr_blocks = re.findall(r'<tr[^>]*data-fixtureid="[^"]*"[^>]*>', html, re.DOTALL)
print('TR blocks found:', len(tr_blocks))

# Show first tr block
if tr_blocks:
    print('\nFirst TR block:')
    print(tr_blocks[0][:1000])

# Check for any match-related patterns
print('\nSearching for matchnum patterns:')
matchnum = re.findall(r'data-matchnum="([^"]*)"', html)
print('matchnum count:', len(matchnum))
print('matchnum:', matchnum[:5])

print('\nSearching for score patterns:')
scores = re.findall(r'data-(?:rq)?score="([^"]*)"', html)
print('score count:', len(scores))
print('scores:', scores[:5])

print('\nSearching for result patterns:')
results = re.findall(r'data-(?:rq)?result="([^"]*)"', html)
print('result count:', len(results))
print('results:', results[:5])
