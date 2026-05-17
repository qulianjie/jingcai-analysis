import requests, re
r = requests.get('https://cp.zgzcw.com/lottery/jcplayvsForJsp.action?lotteryId=23&issue=2026-05-07', timeout=15)
print('length:', len(r.text))
print('first 500:', r.text[:500])
# try different patterns
trs = re.findall(r'mN[=:]"([^"]*)"', r.text)
print('mN variant:', trs[:10])
# try find any tr with day names
trs2 = re.findall(r'<tr[^>]*>', r.text)
print('tr count:', len(trs2))
for t in trs2[:20]:
    print('  ', t[:100])
