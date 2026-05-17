import requests, re

r = requests.get('https://cp.zgzcw.com/lottery/jcplayvsForJsp.action?lotteryId=23&issue=2026-05-07', 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
    timeout=15)
print('Status:', r.status_code)
print('Length:', len(r.text))
print('First 300:', r.text[:300])
if 'CloudWAF' in r.text:
    print('BLOCKED by CloudWAF')
# try to find match results
trs = re.findall(r'mN="([^"]*)"', r.text)
print('mN matches:', trs)
