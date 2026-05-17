# -*- coding: utf-8 -*-
import requests, json, sys, io, re
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# Fetch liansai.500.com homepage
r = sess.get('https://liansai.500.com/', timeout=15)
r.encoding = 'gbk'
html = r.text
print('HTML length:', len(html))

soup = BeautifulSoup(html, 'html.parser')

# Find all links with /zuqiu-{id}/ pattern
league_links = {}
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/zuqiu-(\d+)/', href)
    if m:
        fid = m.group(1)
        name = a.get_text().strip()
        if name:
            if fid not in league_links:
                league_links[fid] = name

print()
print('League links found:', len(league_links))
print()

# Output in a structured format
for fid in sorted(league_links.keys(), key=lambda x: int(x)):
    print('{}\t{}'.format(fid, league_links[fid]))
