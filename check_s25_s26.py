# -*- coding: utf-8 -*-
import json, os

# Find step25/step26 files
tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
for date_dir in ['2026-05-03', '2026-05-04']:
    data_path = os.path.join(tasks_dir, date_dir, 'data')
    if os.path.isdir(data_path):
        for subdir in os.listdir(data_path)[:3]:
            s25 = os.path.join(data_path, subdir, 'step25_zhuangjia.json')
            s26 = os.path.join(data_path, subdir, 'step26_profit_ratio.json')
            print('=== %s/%s ===' % (date_dir, subdir))
            if os.path.exists(s25):
                with open(s25, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print('step25 keys:', sorted(data.keys()))
                if 'labels' in data:
                    for k, v in list(data['labels'].items())[:3]:
                        print('  label %s: %s' % (k, v))
            if os.path.exists(s26):
                with open(s26, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print('step26 keys:', sorted(data.keys()))
                if 'analysis' in data:
                    print('  analysis: %s' % json.dumps(data['analysis'], ensure_ascii=False, indent=2)[:500])
            print()
