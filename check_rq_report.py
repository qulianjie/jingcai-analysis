# -*- coding: utf-8 -*-
import re

f = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-02\周六001_奥克兰FCvs墨尔本城.md'
content = open(f, 'r', encoding='utf-8', errors='replace').read()

# Find 让球预测 in report
m = re.search(r'\*\*让球预测\*\*\s*\|\s*([^\|]+)', content)
if m:
    print('Found 让球预测:', repr(m.group(1)))
else:
    # Show context around 让球
    idx = content.find('让球预测')
    if idx >= 0:
        print('Found at:', idx)
        print(content[idx:idx+200].encode('ascii', errors='replace').decode('ascii'))
    else:
        print('Not found')
        # Show lines around "推荐"
        idx2 = content.find('推荐')
        if idx2 >= 0:
            print('Context around 推荐:')
            print(content[idx2:idx2+300].encode('ascii', errors='replace').decode('ascii'))
