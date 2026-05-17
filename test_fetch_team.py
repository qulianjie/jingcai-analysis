# -*- coding: utf-8 -*-
"""测试 fetch_team 函数"""
import sys, os, json, requests, time
from bs4 import BeautifulSoup

# 使用与 step918 相同的配置
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

def fetch_team(team_id):
    """从 trade.500.com 获取球队历史数据"""
    all_data = []
    page = 1
    while True:
        try:
            url = 'https://trade.500.com/jczq/teamoddschange.php?teamid={}&page={}'.format(team_id, page)
            resp = sess.get(url, timeout=15)
            resp.encoding = 'gbk'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                break
            
            rows = table.find_all('tr')
            if len(rows) <= 1:
                break
            
            for row in rows[1:]:
                tds = row.find_all('td')
                if len(tds) < 10:
                    continue
                all_data.append({
                    'date': tds[1].get_text().strip(),
                    'home': tds[2].get_text().strip(),
                    'away': tds[3].get_text().strip(),
                    'score': tds[4].get_text().strip(),
                    'half': tds[5].get_text().strip(),
                    'result': tds[6].get_text().strip(),
                    'handicap': tds[7].get_text().strip(),
                    'pan': tds[8].get_text().strip(),
                    'bs': tds[9].get_text().strip() if len(tds) > 9 else '',
                })
            
            # 检查是否有下一页
            next_page = soup.find('a', string='下一页')
            if not next_page:
                break
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            print('  [ERROR] page {} failed: {}'.format(page, e))
            break
    
    return all_data

# 测试几个球队
test_teams = ['15541', '2320', '4067', '606']  # 从 meta.json 中获取的 home_id/away_id

for team_id in test_teams:
    print('Testing team_id={}...'.format(team_id))
    start = time.time()
    try:
        data = fetch_team(team_id)
        elapsed = time.time() - start
        print('  OK: {} records in {:.1f}s'.format(len(data), elapsed))
    except Exception as e:
        elapsed = time.time() - start
        print('  FAILED: {} in {:.1f}s'.format(e, elapsed))
