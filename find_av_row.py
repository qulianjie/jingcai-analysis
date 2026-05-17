# -*- coding: utf-8 -*-
"""
查看百家赔率页面的实际结构，找到"百家平均"的正确提取方式
"""
import requests
from bs4 import BeautifulSoup

# 测试一个成功获取到百家数据的match
fid = 1216098  # 比利亚雷亚尔vs塞维利亚 (step19有数据)

sess = requests.Session()
url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
print('URL: %s' % url)

r = sess.get(url, timeout=15)
r.encoding = 'gbk'
soup = BeautifulSoup(r.text, 'html.parser')

results = []

# 查找所有表格
for table_idx, table in enumerate(soup.find_all('table'), 1):
    rows = table.find_all('tr')
    for row_idx, tr in enumerate(rows, 1):
        tds = tr.find_all('td')
        if len(tds) < 6:
            continue
        
        td0 = tds[0].get_text().strip()
        td1 = tds[1].get_text().strip()
        
        # 检查是否包含"平均"相关字符
        if '平均' in td1 or '百家' in td1 or '均值' in td1 or '合计' in td1:
            results.append('FOUND: table=%d row=%d td0=%s td1=%s' % (table_idx, row_idx, td0, td1))
            for i, td in enumerate(tds):
                results.append('  td%d: %s' % (i, td.get_text().strip()[:50]))

# Also show rows 1, 6 (index 0, 5) to see the pattern
results.append('')
results.append('Rows 1, 6 (for comparison):')
for table in soup.find_all('table'):
    rows = table.find_all('tr')
    for row_idx in [0, 5]:
        if row_idx < len(rows):
            tr = rows[row_idx]
            tds = tr.find_all('td')
            if len(tds) < 6:
                continue
            td0 = tds[0].get_text().strip()
            td1 = tds[1].get_text().strip()
            results.append('row[%d]: td0=%s td1=%s' % (row_idx, td0, td1))

with open('jingcai/av_row_info.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/av_row_info.txt')
