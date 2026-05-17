# -*- coding: utf-8 -*-
"""检查step25和step26的原始数据"""
import json, os

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Check 3 matches
for date_dir in ['2026-05-03']:
    data_path = os.path.join(tasks_dir, date_dir, 'data')
    if not os.path.isdir(data_path):
        continue
    
    for subdir in sorted(os.listdir(data_path))[:5]:
        s25_path = os.path.join(data_path, subdir, 'step25_zhuangjia.json')
        s26_path = os.path.join(data_path, subdir, 'step26_profit_ratio.json')
        
        if not os.path.exists(s25_path) or not os.path.exists(s26_path):
            continue
        
        with open(s25_path, 'r', encoding='utf-8') as f:
            s25 = json.load(f)
        with open(s26_path, 'r', encoding='utf-8') as f:
            s26 = json.load(f)
        
        print('=== %s/%s ===' % (date_dir, subdir))
        
        # Step25 raw labels
        labels = s25.get('labels', {})
        print('Step25 labels:')
        for key in ['主胜', '平局', '客胜']:
            if key in labels:
                v = labels[key]
                print('  %s: bet_pct=%s volume=%s profit=%s' % (key, v.get('bet_pct',''), v.get('volume',''), v.get('profit','')))
        
        # Step26 analysis
        analysis = s26.get('analysis', {})
        print('Step26 analysis:')
        print('  庄家胜盈亏: %s' % analysis.get('庄家胜盈亏', ''))
        print('  庄家平盈亏: %s' % analysis.get('庄家平盈亏', ''))
        print('  庄家负盈亏: %s' % analysis.get('庄家负盈亏', ''))
        print('  庄家最看好: %s' % analysis.get('庄家最看好', ''))
        
        # Step26 profit_ratio raw
        profit_ratio = s26.get('profit_ratio', {})
        print('Step26 profit_ratio raw:')
        for key in ['主胜', '平局', '客胜']:
            if key in profit_ratio:
                v = profit_ratio[key]
                print('  %s: ratio=%s profit=%s bet_pct=%s 庄家盈亏=%s' % (key, v.get('ratio',''), v.get('profit',''), v.get('bet_pct',''), v.get('庄家盈亏','')))
        
        print()
