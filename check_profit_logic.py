# -*- coding: utf-8 -*-
"""检查庄家盈亏判断逻辑"""
import json, os

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Check 3 matches with actual results
check_dates = ['2026-05-03']
for date_dir in check_dates:
    data_path = os.path.join(tasks_dir, date_dir, 'data')
    if not os.path.isdir(data_path):
        continue
    
    for subdir in sorted(os.listdir(data_path))[:3]:
        s25_path = os.path.join(data_path, subdir, 'step25_zhuangjia.json')
        s26_path = os.path.join(data_path, subdir, 'step26_profit_ratio.json')
        
        if not os.path.exists(s25_path) or not os.path.exists(s26_path):
            continue
        
        with open(s25_path, 'r', encoding='utf-8') as f:
            s25 = json.load(f)
        with open(s26_path, 'r', encoding='utf-8') as f:
            s26 = json.load(f)
        
        print('=== %s/%s ===' % (date_dir, subdir))
        
        # Show actual result
        score = s26.get('score_dist', {})
        print('Actual score: %s' % s26.get('score_dist', {}))
        
        # Show step25 labels
        labels = s25.get('labels', {})
        print('Step25 labels:')
        for key in ['主胜', '平局', '客胜']:
            if key in labels:
                print('  %s: %s' % (key, labels[key]))
        
        # Show step26 analysis
        analysis = s26.get('analysis', {})
        print('Step26 analysis:')
        print('  庄家胜盈亏: %s' % analysis.get('庄家胜盈亏', ''))
        print('  庄家平盈亏: %s' % analysis.get('庄家平盈亏', ''))
        print('  庄家负盈亏: %s' % analysis.get('庄家负盈亏', ''))
        
        # Show profit_ratio
        profit_ratio = s26.get('profit_ratio', {})
        print('Profit ratio raw:')
        for key, val in profit_ratio.items():
            print('  %s: %s' % (key, val))
        
        print()
