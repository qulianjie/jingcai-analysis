# -*- coding: utf-8 -*-
"""重跑010-030所有场次"""
import os, sys, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from run_pipeline import fetch_matches, run_match_pipeline, organize_data, log

DATE = '2026-05-02'
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def main():
    matches = fetch_matches(DATE)
    if not matches:
        log('ERROR', '没有找到比赛数据')
        return
    
    log('INFO', '共 {} 场比赛'.format(len(matches)))
    
    success = 0
    for i, match in enumerate(matches):
        match_num = match.get('matchnum', str(i + 1))
        num = int(match_num) if match_num.isdigit() else 0
        
        # 只跑010-030
        if num < 10 or num > 30:
            continue
        
        log('RUN', '正在跑 {} ({} vs {})'.format(match_num, match.get('home', '?'), match.get('away', '?')))
        ok = run_match_pipeline(match, DATE, match_num)
        if ok:
            success += 1
            log('OK', '{} 完成'.format(match_num))
        else:
            log('FAIL', '{} 失败'.format(match_num))
    
    organize_data(DATE)
    log('DONE', '010-030 完成: 成功 {}/{}'.format(success, 21))

if __name__ == '__main__':
    main()
