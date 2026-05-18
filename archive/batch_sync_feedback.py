#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补跑5月1日~5月6日的 Notion 同步 + Feedback
不重新跑24步分析（已有旧数据），只执行：
  1. sync_notion.js add {date}  - 同步到Notion
  2. feedback.js --date {date}  - 反馈更新（终盘赔率+比分+预测正确性）
"""
import os, sys, subprocess, time

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DATES = ['2026-05-01', '2026-05-02', '2026-05-03',
         '2026-05-04', '2026-05-05', '2026-05-06']

def log(msg):
    print('[BATCH] ' + str(msg))
    sys.stdout.flush()

def run_node(script, args, timeout=300):
    cmd = ['node', os.path.join(SCRIPT_DIR, script)] + args
    log('CMD: ' + ' '.join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, encoding='utf-8', errors='replace')
        for line in (result.stdout or '').split('\n'):
            s = line.strip()
            if s and (s.startswith('[OK]') or s.startswith('[' + u'\u7ECF\u9A8C' + ']') or 
                      s.startswith('[STEPS OK]') or s.startswith(u'\u2744') or
                      '已更新' in s or '已跳过' in s or '已同步' in s or
                      '写入' in s or '清空' in s or '完成' in s or
                      'feedback' in s.lower() or '终盘' in s or '📝' in s or '✅' in s or '❌' in s):
                log('  ' + s)
        if result.returncode != 0:
            for line in (result.stderr or '').split('\n')[:3]:
                if line.strip():
                    log('  ERR: ' + line.strip()[:200])
            return False
        return True
    except subprocess.TimeoutExpired:
        log('  TIMEOUT')
        return False
    except Exception as e:
        log('  EXCEPTION: ' + str(e))
        return False

def main():
    log('=' * 50)
    log('Batch sync+feedback 05-01 ~ 05-06')
    log('=' * 50)
    
    for date_str in DATES:
        log('')
        log('>>> ' + date_str)
        
        # Step 1: Notion 同步
        log('--- Notion Sync ---')
        ok = run_node('sync_notion.js', ['add', date_str], timeout=180)
        
        # Step 2: Feedback
        log('--- Feedback ---')
        ok2 = run_node('feedback.js', ['--date', date_str], timeout=180)
        
        if ok and ok2:
            log('OK: ' + date_str)
        else:
            log('WARN: ' + date_str + ' sync=' + str(ok) + ' feedback=' + str(ok2))
        
        # 间隔
        if date_str != DATES[-1]:
            log('rest 15s...')
            time.sleep(15)
    
    log('')
    log('=' * 50)
    log('ALL DONE')
    log('=' * 50)

if __name__ == '__main__':
    main()
