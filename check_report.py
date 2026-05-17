# -*- coding: utf-8 -*-
import os, re
f = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-02/周六001_奥克兰FCvs墨尔本城.md'
content = open(f, 'r', encoding='utf-8', errors='replace').read()

# Find the recommendation line
m = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
if m:
    print('Recommendation:', repr(m.group(1)))
else:
    print('No recommendation found')
    # Show context around "最终预测"
    idx = content.find('最终预测分析')
    if idx >= 0:
        snippet = content[idx:idx+500]
        for line in snippet.split('\n')[:15]:
            print('LINE:', repr(line))
    else:
        # Show last 500 chars
        print('No conclusion section found')
        print(content[-500:])
