# -*- coding: utf-8 -*-
"""从 sporttery.cn 全量提取竞彩联赛简称"""
import requests, json, os, re
from bs4 import BeautifulSoup

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 1. 从 sporttery.cn 获取竞彩足球比赛列表
url = 'https://sporttery.cn/jc/jczq/'
print(f'获取竞彩足球页面: {url}')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

try:
    resp = sess.get(url, timeout=15)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 查找所有联赛链接
    leagues = set()
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        # 联赛链接通常包含 leagueId 或类似参数
        if 'league' in href.lower() or 'leagueId' in href:
            text = a.get_text().strip()
            if text and len(text) > 1:
                leagues.add(text)
    
    print(f'从 sporttery.cn 找到 {len(leagues)} 个联赛')
    for l in sorted(leagues):
        print(f'  {l}')
except Exception as e:
    print(f'sporttery.cn 获取失败: {e}')

# 2. 从 odds.500.com 提取联赛名
print('\n从 odds.500.com 提取...')
try:
    # 获取今天的比赛
    resp2 = sess.get('https://odds.500.com/jczq/index.shtml', timeout=15)
    resp2.encoding = 'gbk'
    soup2 = BeautifulSoup(resp2.text, 'html.parser')
    
    leagues2 = set()
    for span in soup2.find_all('span', class_=re.compile('league|simpleleague')):
        text = span.get_text().strip()
        if text and len(text) > 1:
            leagues2.add(text)
    
    # 从 data-simpleleague 属性提取
    for div in soup2.find_all('div', attrs={'data-simpleleague': True}):
        league = div.get('data-simpleleague', '').strip()
        if league:
            leagues2.add(league)
    
    print(f'从 odds.500.com 找到 {len(leagues2)} 个联赛')
    for l in sorted(leagues2):
        print(f'  {l}')
except Exception as e:
    print(f'odds.500.com 获取失败: {e}')

# 3. 从 liansai.500.com 获取完整联赛列表
print('\n从 liansai.500.com 获取完整联赛列表...')
try:
    resp3 = sess.get('https://liansai.500.com/', timeout=15)
    resp3.encoding = 'gbk'
    soup3 = BeautifulSoup(resp3.text, 'html.parser')
    
    leagues3 = []
    for a in soup3.find_all('a', href=re.compile(r'/zuqiu-\d+/')):
        href = a.get('href', '')
        text = a.get_text().strip()
        if text and '/zuqiu-' in href:
            league_id = re.search(r'/zuqiu-(\d+)/', href)
            if league_id:
                leagues3.append({
                    'id': league_id.group(1),
                    'name': text
                })
    
    print(f'从 liansai.500.com 找到 {len(leagues3)} 个联赛')
    
    # 保存到文件
    out_path = os.path.join(SCRIPT_DIR, 'leagues_from_liansai.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(leagues3, f, ensure_ascii=False, indent=2)
    print(f'已保存到: {out_path}')
    
except Exception as e:
    print(f'liansai.500.com 获取失败: {e}')

# 4. 合并所有联赛名
all_league_names = set()
all_league_names.update(leagues)
all_league_names.update(leagues2)
for l in leagues3:
    all_league_names.add(l['name'])

print(f'\n合并后总计: {len(all_league_names)} 个联赛名')

# 5. 与 leagues_all.json 对比
existing_path = os.path.join(SCRIPT_DIR, 'leagues_all.json')
if os.path.exists(existing_path):
    with open(existing_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    existing_names = set(l['name'] for l in existing)
    
    new_names = all_league_names - existing_names
    missing_names = existing_names - all_league_names
    
    print(f'\n对比 leagues_all.json ({len(existing)} 个):')
    print(f'  新增: {len(new_names)} 个')
    print(f'  缺失: {len(missing_names)} 个')
    
    if new_names:
        print('  新增联赛:')
        for n in sorted(new_names)[:20]:
            print(f'    + {n}')
