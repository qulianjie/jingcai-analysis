# -*- coding: utf-8 -*-
"""检查001报告的各维度信号明细表"""
import os

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        # Find dimension table
        print('=== 各维度信号明细 ===')
        in_dim = False
        for line in content.split('\n'):
            if '各维度信号明细' in line:
                in_dim = True
            if in_dim:
                safe = ''.join(c if ord(c) < 128 else '?' for c in line)
                print('  %s' % safe[:150])
                if line.strip().startswith('---'):
                    break
        
        # Find all table rows with key labels
        print('\n=== 关键标签 ===')
        for label in ['欧赔趋势', 'IW同赔', '澳门亚盘', '主队主场', '客队客场', '百家对比', '欧赔组合']:
            found = False
            for line in content.split('\n'):
                if label in line and '|' in line:
                    safe = ''.join(c if ord(c) < 128 else '?' for c in line)
                    print('  %s: %s' % (label, safe[:150]))
                    found = True
                    break
            if not found:
                print('  %s: NOT FOUND' % label)
        break
