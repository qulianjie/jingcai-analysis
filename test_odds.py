# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

r = requests.get('https://odds.500.com/fenxi/ouzhi-1206140.shtml', timeout=10, headers={'User-Agent':'Mozilla/5.0'})
r.encoding = 'gbk'
soup = BeautifulSoup(r.text, 'html.parser')

found = 0
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12:
            continue
        name = tds[1].get_text().strip()
        if name in ['竞彩官方', 'Interwetten', '百家平均']:
            nums = []
            for idx in [3,4,5,6,7,8]:
                val = tds[idx].get_text().strip().replace('\xa0', '')
                try:
                    nums.append(float(val))
                except:
                    pass
            if len(nums) >= 6:
                found += 1
                print(f"[{found}] {name}: 初盘={nums[0]}/{nums[1]}/{nums[2]} 即时={nums[3]}/{nums[4]}/{nums[5]}")

print(f'\nTotal found: {found}')
