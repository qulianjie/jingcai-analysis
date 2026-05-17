# -*- coding: utf-8 -*-
"""
竞彩工作区保护脚本
用法: python jingcai/protect.py [命令]
命令:
  status          显示当前工作区状态（运行中的脚本、锁、活跃match）
  lock <name>     获取命名锁
  unlock <name>   释放命名锁
  list-locks      列出所有锁
  list-active     列出正在处理的match
  clean-stale     清理过期锁/标记
"""
import os, sys, json, time
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
LOCK_DIR = os.path.join(WORKSPACE, '.locks')
MARKER_DIR = os.path.join(WORKSPACE, '.markers')

def ensure_dirs():
    os.makedirs(LOCK_DIR, exist_ok=True)
    os.makedirs(MARKER_DIR, exist_ok=True)

def _get_running_python_procs():
    """获取正在运行的Python进程及其命令行"""
    import subprocess
    procs = []
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-CimInstance Win32_Process -Filter "Name=\'python.exe\'" | '
             'Select-Object ProcessId,CommandLine | ConvertTo-Json'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            if isinstance(data, dict):
                data = [data]
            for p in data:
                cmdline = p.get('CommandLine', '')
                if 'jingcai' in cmdline or '自媒体' in cmdline or 'xiaohongshu' in cmdline:
                    procs.append({
                        'pid': p['ProcessId'],
                        'cmdline': cmdline
                    })
    except Exception as e:
        print('[protect] 获取进程失败: %s' % e)
    return procs

def lock(name, timeout=0):
    """获取命名锁。name='batch', 'pipeline', 'step0'等"""
    ensure_dirs()
    lock_file = os.path.join(LOCK_DIR, '%s.lock' % name)
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            lock_time = datetime.strptime(info['time'], '%Y-%m-%d %H:%M:%S')
            age = (datetime.now() - lock_time).total_seconds()
            if age > 7200:  # 2小时过期
                print('[protect] 锁 %s 已过期 (age=%.0fs)，清理' % (name, age))
                os.remove(lock_file)
            else:
                print('[protect] 锁 %s 已被占用:' % name)
                print('  PID: %s' % info['pid'])
                print('  脚本: %s' % info.get('script', 'unknown'))
                print('  时间: %s' % info['time'])
                print('  已运行: %.0fs' % age)
                if timeout > 0:
                    print('[protect] 等待 %ds 后重试...' % timeout)
                    time.sleep(timeout)
                    return lock(name, 0)
                return False
        except (json.JSONDecodeError, KeyError, ValueError):
            os.remove(lock_file)
    
    info = {
        'pid': os.getpid(),
        'script': os.path.basename(sys.argv[0]),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'session': os.environ.get('OPENCLAW_SESSION_KEY', 'unknown')
    }
    with open(lock_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print('[protect] OK 锁 %s 已获取 (PID %s)' % (name, os.getpid()))
    return True

def unlock(name):
    """释放命名锁"""
    ensure_dirs()
    lock_file = os.path.join(LOCK_DIR, '%s.lock' % name)
    if not os.path.exists(lock_file):
        print('[protect] 锁 %s 不存在' % name)
        return False
    try:
        with open(lock_file, 'r', encoding='utf-8') as f:
            info = json.load(f)
        if info['pid'] != os.getpid():
            print('[protect] 锁 %s 不是当前进程持有 (PID %s)' % (name, info['pid']))
            return False
        os.remove(lock_file)
        print('[protect] OK 锁 %s 已释放' % name)
        return True
    except Exception as e:
        print('[protect] 释放锁失败: %s' % e)
        return False

def list_locks():
    """列出所有锁"""
    ensure_dirs()
    locks = []
    for f in sorted(os.listdir(LOCK_DIR)):
        if not f.endswith('.lock'):
            continue
        name = f[:-5]
        lock_file = os.path.join(LOCK_DIR, f)
        try:
            with open(lock_file, 'r', encoding='utf-8') as fh:
                info = json.load(fh)
            lock_time = datetime.strptime(info['time'], '%Y-%m-%d %H:%M:%S')
            age = (datetime.now() - lock_time).total_seconds()
            status = 'STALE' if age > 7200 else 'ACTIVE'
            locks.append({
                'name': name,
                'pid': info['pid'],
                'script': info.get('script', '?'),
                'time': info['time'],
                'age': '%.0fs' % age,
                'session': info.get('session', '?'),
                'status': status
            })
        except Exception:
            locks.append({'name': name, 'status': 'BROKEN'})
    return locks

def mark_match(date, match_num):
    """标记match正在处理"""
    ensure_dirs()
    key = '%s_%03d' % (date, match_num)
    marker_file = os.path.join(MARKER_DIR, '%s.marker' % key)
    with open(marker_file, 'w', encoding='utf-8') as f:
        json.dump({
            'pid': os.getpid(),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'session': os.environ.get('OPENCLAW_SESSION_KEY', 'unknown')
        }, f, ensure_ascii=False, indent=2)

def unmark_match(date, match_num):
    """清除match标记"""
    ensure_dirs()
    key = '%s_%03d' % (date, match_num)
    marker_file = os.path.join(MARKER_DIR, '%s.marker' % key)
    if os.path.exists(marker_file):
        os.remove(marker_file)

def list_active_matches():
    """列出正在处理的match"""
    ensure_dirs()
    matches = []
    for f in sorted(os.listdir(MARKER_DIR)):
        if not f.endswith('.marker'):
            continue
        key = f[:-7]
        marker_file = os.path.join(MARKER_DIR, f)
        try:
            with open(marker_file, 'r', encoding='utf-8') as fh:
                info = json.load(fh)
            matches.append({
                'match': key,
                'pid': info['pid'],
                'time': info['time'],
                'session': info.get('session', '?')
            })
        except Exception:
            matches.append({'match': key, 'status': 'BROKEN'})
    return matches

def clean_stale():
    """清理过期锁和标记"""
    ensure_dirs()
    removed = 0
    for f in os.listdir(LOCK_DIR):
        if not f.endswith('.lock'):
            continue
        lock_file = os.path.join(LOCK_DIR, f)
        try:
            with open(lock_file, 'r', encoding='utf-8') as fh:
                info = json.load(fh)
            lock_time = datetime.strptime(info['time'], '%Y-%m-%d %H:%M:%S')
            age = (datetime.now() - lock_time).total_seconds()
            if age > 7200:
                os.remove(lock_file)
                print('[protect] 清理过期锁: %s (%.0fs)' % (f[:-5], age))
                removed += 1
        except Exception:
            os.remove(lock_file)
            print('[protect] 清理损坏锁: %s' % f[:-5])
            removed += 1
    
    for f in os.listdir(MARKER_DIR):
        if not f.endswith('.marker'):
            continue
        marker_file = os.path.join(MARKER_DIR, f)
        try:
            with open(marker_file, 'r', encoding='utf-8') as fh:
                info = json.load(fh)
            try:
                os.kill(info['pid'], 0)
            except (ProcessLookupError, PermissionError):
                os.remove(marker_file)
                print('[protect] 清理死标记: %s' % f[:-7])
                removed += 1
        except Exception:
            os.remove(marker_file)
            print('[protect] 清理损坏标记: %s' % f[:-7])
            removed += 1
    print('[protect] 清理完成: 移除 %d 项' % removed)
    return removed

def status():
    """显示完整状态"""
    print('=' * 70)
    print('  JingCai Workspace Status')
    print('=' * 70)
    
    # Running Python processes
    procs = _get_running_python_procs()
    print('\nRunning Python processes (%d):' % len(procs))
    if procs:
        for p in procs:
            cmd = p['cmdline']
            if 'batch_full' in cmd:
                script = 'batch_full.py'
            elif 'run_pipeline' in cmd:
                script = 'run_pipeline.py'
            elif 'step0' in cmd:
                script = 'step0_fetch_matches.py'
            elif 'step24' in cmd:
                script = 'step24_extractor.py'
            else:
                script = cmd[-60:]
            print('  PID %6d  %s' % (p['pid'], script))
    else:
        print('  (none)')
    
    # Locks
    locks = list_locks()
    print('\nLocks (%d):' % len(locks))
    if locks:
        print('  %-25s %7s %-8s %s' % ('Name', 'PID', 'Status', 'Age'))
        print('  ' + '-' * 65)
        for l in locks:
            print('  %-25s %7s %-8s %s' % (l['name'], str(l.get('pid','')), l['status'], l.get('age','')))
    else:
        print('  (none)')
    
    # Active matches
    matches = list_active_matches()
    print('\nActive matches (%d):' % len(matches))
    if matches:
        for m in matches:
            print('  %-25s PID %6d  %s' % (m['match'], m['pid'], m['time']))
    else:
        print('  (none)')
    
    print()

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        status()
        print('用法: python jingcai/protect.py [命令]')
        print('命令:')
        print('  status            显示工作区状态')
        print('  lock <name>       获取命名锁')
        print('  unlock <name>     释放命名锁')
        print('  list-locks        列出所有锁')
        print('  list-active       列出活跃match')
        print('  clean-stale       清理过期锁/标记')
        sys.exit(0)
    
    cmd = args[0]
    if cmd == 'status':
        status()
    elif cmd == 'lock' and len(args) >= 2:
        ok = lock(args[1])
        sys.exit(0 if ok else 1)
    elif cmd == 'unlock' and len(args) >= 2:
        ok = unlock(args[1])
        sys.exit(0 if ok else 1)
    elif cmd == 'list-locks':
        locks = list_locks()
        for l in locks:
            print('%-25s PID=%s  %s  %s' % (l['name'], l.get('pid','?'), l['status'], l.get('age','')))
    elif cmd == 'list-active':
        matches = list_active_matches()
        for m in matches:
            print('%-25s PID=%d  %s' % (m['match'], m['pid'], m['time']))
    elif cmd == 'clean-stale':
        clean_stale()
    else:
        print('未知命令: %s' % cmd)
        sys.exit(1)
