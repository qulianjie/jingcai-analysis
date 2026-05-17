# -*- coding: utf-8 -*-
import urllib.request
import sys

url = 'https://trade.500.com/jczq/?playid=271&g=2&date=2026-04-03'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://trade.500.com/jczq/',
})
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')

# 打印前10000个字符看看结构
print(html[:10000])
