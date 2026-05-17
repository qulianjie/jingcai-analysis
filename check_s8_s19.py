#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查哪些task缺失step8/step19-23"""
import os, glob, json

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

log_path = os.path.join(SCRIPT_DIR, 'check_step8_19_missing_log.txt')
with open(log_path, 'w', encoding='utf-8') as log:
    for date in ['2026-05-08', '2026-05-09', '2026-05-12', '2026-05-13']:
        data_dir = os.path.join(TASKS_DIR, date, 'data')
        if not os.path.isdir(data_dir):
            log.write('{}: NO DATA\n'.format(date))
            continue
        
        tasks = sorted([os.path.basename(d.rstrip('\\')) for d in glob.glob(data_dir + '\\match*\\')])
        missing_any = 0
        
        for t in tasks:
            tdir = os.path.join(data_dir, t)
            meta_file = os.path.join(tdir, 'meta.json')
            s8 = os.path.join(tdir, 'group03_asian', 'step8_same_league.txt')
            s19 = os.path.join(tdir, 'group06_baijia', 'step19_baijia_compare.txt')
            
            if not os.path.isfile(s8) or not os.path.isfile(s19):
                missing_any += 1
                # 读meta（如存在）
                fid = league = ''
                if os.path.isfile(meta_file):
                    with open(meta_file, encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    try:
                        meta = json.loads(content)
                        fid = meta.get('fid', '')
                        league = meta.get('league', '')
                    except:
                        pass
                
                log.write('{}|{}|MISS: s8={} s19={} fid={} league={}\n'.format(
                    date, t[:45], 'OK' if os.path.isfile(s8) else 'NO',
                    'OK' if os.path.isfile(s19) else 'NO',
                    fid, league))
        
        total = len(tasks)
        if missing_any > 0:
            log.write('\n{}: {}/{} tasks missing step8 or step19\n\n'.format(date, missing_any, total))
        else:
            log.write('{}: ALL OK ({})\n\n'.format(date, total))

print('Log:', log_path)
