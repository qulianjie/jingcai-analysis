# -*- coding: utf-8 -*-
import urllib.request
url = 'https://trade.500.com/jczq/?playid=271&g=2&date=2026-04-03'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')
with open('test_500.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('OK len=' + str(len(html)))
