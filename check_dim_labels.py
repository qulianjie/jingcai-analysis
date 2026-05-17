# -*- coding: utf-8 -*-
"""检查报告里各维度信号明细的实际标签"""
import os

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        # Find 各维度信号明细 section
        idx = content.find('各维度信号明细')
        if idx >= 0:
            section = content[idx:idx+1000]
            print('=== 各维度信号明细 section ===')
            for line in section.split('\n'):
                if '|' in line and '---' not in line and line.strip().startswith('|'):
                    print('  %s' % line.strip()[:150])
        else:
            print('No 各维度信号明细 found')
        
        # Also check for specific labels
        print('\n=== Label search ===')
        for label in ['欧赔趋势', 'IW同赔', '澳门亚盘', '主队主场', '客队客场', '百家对比', '欧赔组合', '竞彩同赔', '盘路匹配', '庄家盈亏']:
            for line in content.split('\n'):
                if label in line and '|' in line and '---' not in line:
                    safe = ''.join(c if ord(c) < 128 else '?' for c in line.strip())
                    print('  %s: %s' % (label, safe[:150]))
                    break
        break
