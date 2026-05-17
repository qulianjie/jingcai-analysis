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

# Find the first match row and show the full <tr>...</tr>
tr_blocks = re.findall(r'<tr[^>]*data-fixtureid="[^"]*"[^>]*>.*?</tr>', html, re.DOTALL)
if tr_blocks:
    print('=== First match row ===')
    print(tr_blocks[0][:2000])
    print('\n=== All data-* attributes ===')
    attrs = re.findall(r'data-([a-z-]+)="([^"]*)"', tr_blocks[0])
    for name, val in attrs:
        print(f'  {name} = {val}')
