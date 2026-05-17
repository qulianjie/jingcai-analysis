# -*- coding: utf-8 -*-
import requests
import re
from datetime import datetime

date_str = '2026-05-13'
target_date = datetime.strptime(date_str, '%Y-%m-%d')
day_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
expected_day = day_names[target_date.weekday()]
print(f'Expected day: {expected_day} ({date_str})')

r = requests.get(f'https://trade.500.com/jczq/?playid=269&g=2&date={date_str}', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
html = r.content.decode('gbk', errors='ignore')
trs = re.findall(r'<tr[^>]*data-fixtureid="[^"]*"[^>]*>', html)

for t in trs:
    num_m = re.search(r'data-matchnum="([^"]*)"', t)
    time_m = re.search(r'data-matchtime="([^"]*)"', t)
    if num_m:
        num = num_m.group(1)
        day_prefix = num[:2]
        match_time = time_m.group(1) if time_m else '?'
        print(f'  {num} time={match_time} day={day_prefix} expected={expected_day}')
