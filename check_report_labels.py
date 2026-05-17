# -*- coding: utf-8 -*-
import os
d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        labels = ['欧赔趋势', 'IW同赔', '澳门亚盘', '百家对比', '欧赔组合', '主队主场', '客队客场', '让球趋势', '亚盘趋势', '让球同赔', '竞彩同赔']
        for label in labels:
            found = label in content
            print('%s: %s' % (label, 'FOUND' if found else 'NOT FOUND'))
        
        # Also check the table section
        print()
        print('=== Table rows ===')
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|') and '欧赔' in stripped or stripped.startswith('|') and '让球' in stripped or stripped.startswith('|') and '亚盘' in stripped or stripped.startswith('|') and '百家' in stripped:
                print(stripped[:150])
