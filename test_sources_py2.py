import urllib.request
import re

# 测试 sporttery.cn
print('=== 测试 sporttery.cn ===')
try:
    req = urllib.request.Request('https://www.sporttery.cn/jc/zqsgkj/', 
        headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read().decode('utf-8', errors='replace')
        print('Status:', r.status)
        print('Length:', len(data))
        scores = re.findall(r'\d+:\d+', data)
        print('Found scores:', len(scores))
        print('Content:', data[:500])
except Exception as e:
    print('Error:', e)

# 测试 okooo.com
print('\n=== 测试 okooo.com ===')
try:
    req2 = urllib.request.Request('https://m.okooo.com/kaijiang/sport.php?LotteryType=SportteryNWDL&LotteryNo=2026-05-10',
        headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2, timeout=10) as r:
        data2 = r.read()
        # 尝试GBK解码
        html = data2.decode('gbk', errors='replace')
        
        print('Status:', r.status)
        print('Length:', len(html))
        
        # 保存
        with open(r'c:\temp\okooo_decoded.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 提取所有比赛数据
        # 格式: 编号 + 主队 + VS + 客队 + 半场比分:全场比分
        pattern = r'(\d{3})\s*\n?\s*(.*?)\s*VS\s*(.*?)\s*(\d+:\d+)\s*.*?(\d+:\d+)'
        matches = re.findall(pattern, html, re.DOTALL)
        
        print(f'\nFound {len(matches)} matches')
        for m in matches[:10]:
            print(f'  {m[0].strip()}: {m[1].strip()} VS {m[2].strip()} 半场{m[3].strip()} 全场{m[4].strip()}')
        
        # 尝试更简单的模式
        # 找所有编号+比分
        simple_pattern = r'(\d{3})\s*\n?\s*.*?VS\s*\n?\s*.*?(\d+:\d+)'
        simple_matches = re.findall(simple_pattern, html, re.DOTALL)
        print(f'\nSimple pattern found {len(simple_matches)} matches')
        for m in simple_matches[:10]:
            print(f'  {m[0].strip()}: {m[1].strip()}')
        
        print('\nContent:', html[:1000])
except Exception as e:
    print('Error:', e)
