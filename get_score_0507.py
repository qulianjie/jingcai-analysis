import requests, re, json

# 获取5-07比分
urls = [
    'https://odds.500.com/schj.shtml',
    'https://f.sporttery.cn/jczq/sc/20260507',
]

# 先试sporttery
try:
    r = requests.get('https://www.sporttery.cn/jc/zqfc', headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }, timeout=10)
    print('sporttery length:', len(r.text))
    print('sporttery status:', r.status_code)
except Exception as e:
    print('sporttery error:', e)

# 再试500
try:
    r2 = requests.get('https://odds.500.com/schj.shtml', headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }, timeout=10)
    print('500 length:', len(r2.text))
    print('500 status:', r2.status_code)
except Exception as e:
    print('500 error:', e)
