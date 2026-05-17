# -*- coding: utf-8 -*-
import urllib.request
import sys
import os

url = 'https://trade.500.com/jczq/?playid=271&g=2&date=2026-04-03'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://trade.500.com/jczq/',
})
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')

# Save to file to inspect
with open('test_fetch_raw.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Saved to test_fetch_raw.html')
print('Length:', len(html))
