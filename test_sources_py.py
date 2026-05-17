import requests
import re

# 测试 sporttery.cn
print('=== 测试 sporttery.cn ===')
try:
    r = requests.get('https://www.sporttery.cn/jc/zqsgkj/', timeout=10)
    print('Status:', r.status_code)
    print('Length:', len(r.text))
    # 检查比分
    scores = re.findall(r'\d+:\d+', r.text)
    print('Found scores:', len(scores))
    print('Content:', r.text[:500])
except Exception as e:
    print('Error:', e)

# 测试 okooo.com
print('\n=== 测试 okooo.com ===')
try:
    r2 = requests.get('https://m.okooo.com/kaijiang/sport.php?LotteryType=SportteryNWDL&LotteryNo=2026-05-10', timeout=10)
    r2.encoding = 'gbk'
    print('Status:', r2.status_code)
    print('Length:', len(r2.text))
    
    # 保存HTML
    with open(r'c:/temp/okooo_decoded.html', 'w', encoding='utf-8') as f:
        f.write(r2.text)
    
    # 提取所有比赛数据
    # 格式: 编号 + 球队名 + VS + 球队名 + 比分
    pattern = r'(\d{3})\s*\n?\s*(.*?)\s*VS\s*(.*?)\s*(\d+:\d+)'
    matches = re.findall(pattern, r2.text, re.DOTALL)
    
    print(f'\nFound {len(matches)} matches')
    for m in matches[:5]:
        print(f'  {m[0]}: {m[1].strip()} VS {m[2].strip()} {m[3].strip()}')
    
    print('\nContent:', r2.text[:1000])
except Exception as e:
    print('Error:', e)
