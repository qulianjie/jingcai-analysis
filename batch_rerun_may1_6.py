#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量重跑竞彩5月1日~5月6日（逐天释放锁+分析+Notion同步+Feedback）
已修复GBK编码问题，无emoji
"""
import os, sys, subprocess, time

# 解决GBK编码问题
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCKS_DIR = os.path.join(SCRIPT_DIR, '.locks')

# 根据当前时间决定范围
DATES = ['2026-05-01', '2026-05-02', '2026-05-03',
         '2026-05-04', '2026-05-05', '2026-05-06']

def log(msg):
    print('[BATCH] {}'.format(msg))
    sys.stdout.flush()

def release_lock(date_str):
    lock_name = 'pipeline_' + date_str
    protect = os.path.join(SCRIPT_DIR, 'protect.py')
    if os.path.exists(protect):
        try:
            subprocess.run([sys.executable, protect, 'unlock', lock_name],
                         capture_output=True, text=True, timeout=10)
        except:
            pass
    lock_file = os.path.join(LOCKS_DIR, lock_name + '.lock')
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            log('removed lock: ' + lock_file)
        except:
            pass
    # 清空所有锁
    try:
        for f in os.listdir(LOCKS_DIR):
            fp = os.path.join(LOCKS_DIR, f)
            if os.path.isfile(fp):
                os.remove(fp)
    except:
        pass

def run_date(date_str):
    log('')
    log('=' * 50)
    log('>>> ' + date_str)
    log('=' * 50)

    release_lock(date_str)

    pipeline = os.path.join(SCRIPT_DIR, 'run_pipeline.py')
    log('CMD: python run_pipeline.py ' + date_str)

    try:
        result = subprocess.run(
            [sys.executable, pipeline, date_str],
            capture_output=True, text=True,
            timeout=7200,
            encoding='utf-8', errors='replace'
        )

        stdout = result.stdout or ''
        stderr = result.stderr or ''

        # 打印关键行
        for line in stdout.split('\n'):
            s = line.strip()
            if not s:
                continue
            if '[DONE]' in s:
                log('OK ' + s)
            elif '[ERROR]' in s or '[FAIL]' in s:
                log('ERR ' + s)
            elif '已更新' in s or '已跳过' in s or '已同步' in s:
                log('   ' + s)

        if result.returncode != 0:
            log('WARN: exit code ' + str(result.returncode))
            for line in stderr.split('\n')[:5]:
                if line.strip():
                    log(' STDERR: ' + line.strip()[:200])
            return False
        else:
            log('OK: ' + date_str + ' done')
            return True

    except subprocess.TimeoutExpired:
        log('TIMEOUT: ' + date_str)
        return False
    except Exception as e:
        log('EXCEPTION: ' + str(e))
        return False

def main():
    log('Batch rerun jingcai 05-01 ~ 05-06')
    log('Total ' + str(len(DATES)) + ' days')
    log('')

    ok = 0
    fail = 0
    for date_str in DATES:
        if run_date(date_str):
            ok += 1
        else:
            fail += 1
        if date_str != DATES[-1]:
            log('rest 30s...')
            time.sleep(30)

    log('')
    log('=' * 50)
    log('ALL DONE: ' + str(ok) + ' OK, ' + str(fail) + ' FAIL')
    log('=' * 50)

if __name__ == '__main__':
    main()
