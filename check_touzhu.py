# -*- coding: utf-8 -*-
import requests, re

url = 'https://odds.500.com/fenxi/touzhu-1202680.shtml'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = 'gb2312'

# 找主胜相关的数据
idx = resp.text.find('主胜')
if idx > 0:
    print(resp.text[idx:idx+500])
else:
    print('未找到主胜')
