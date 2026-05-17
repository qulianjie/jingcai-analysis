# -*- coding: utf-8 -*-
"""
工作区保护脚本 - 防止多 session 误操作
用途：
  1. 检测正在运行的脚本进程
  2. 防止同时运行冲突脚本
  3. 标记正在使用的目录
  4. 安全清理（只清理已完成的）
"""
import os, sys, json, time, signal, hashlib
from datetime import datetime
from pathlib import Path

WORKSPACE = os.path.join(os.path.expanduser('~'), '.openclaw', 'workspace')
JINGCAI_DIR = os.path.join(WORKSPACE, 'jingcai')
LOCK_DIR = os.path.join(JINGCAI_DIR, '.locks')
MARKER_DIR = os.path.join(JINGCAI_DIR, '.markers')

def ensure_dirs():
    os.makedirs(LOCK_DIR, exist_ok=True)
    os.makedirs(MARKER_DIR, exist_ok=True)

def _pid_file(name):
    return os.path.join(LOCK_DIR, f'{name}.pid')

def _marker_file(date, match_num):
    return os.path.join(MARKER_DIR, f'{date}_{match_num}.marker')

def acquire_lock(name, timeout=0):
    """
    获取命名锁，防止多实例同时运行
    name: 锁名称，如 'batch_full', 'pipeline', 'step0'
    timeout: 0=不等待，>0=等待秒数
    返回: True 成功, False 已有其他实例在运行
    """
    ensure_dirs()
    pid_file = _pid_file(name)
    
    # 检查是否已有锁
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                existing_pid = int(f.read().strip())
            # 检查进程是否还活着
            try:
                os.kill(existing_pid, 0)  # 发送信号0检查进程
                print(f'[LOCK] {name} 已被 PID {existing_pid} 占用')
                if timeout > 0:
                    print(f'[LOCK] 等待 {timeout}s...')
                    time.sleep(timeout)
                    return acquire_lock(name, 0)  # 重试
                return False
            except (ProcessLookupError, PermissionError):
                # 进程不存在了，清理死锁
                print(f'[LOCK] 清理死锁 {name} (PID {existing_pid} 已不存在)')
                os.remove(pid_file)
        except (ValueError, OSError) as e:
            print(f'[LOCK] 损坏的锁文件 {name}: {e}')
            try:
                os.remove(pid_file)
            except:
                pass
    
    # 创建锁
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    print(f'[LOCK] ✓ 获取锁: {name} (PID {os.getpid()})')
    return True

def release_lock(name):
    """释放命名锁"""
    ensure_dirs()
    pid_file = _pid_file(name)
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(pid_file)
                print(f'[LOCK] ✓ 释放锁: {name}')
            else:
                print(f'[LOCK] ⚠ 锁 {name} 不是当前进程持有')
        except:
            pass

def mark_match_in_progress(date, match_num):
    """标记某个 match 正在处理中"""
    ensure_dirs()
    marker = _marker_file(date, match_num)
    with open(marker, 'w') as f:
        json.dump({
            'pid': os.getpid(),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'session': os.environ.get('OPENCLAW_SESSION_KEY', 'unknown')
        }, f, ensure_ascii=False)

def unmark_match(date, match_num):
    """清除 match 处理标记"""
    ensure_dirs()
    marker = _marker_file(date, match_num)
    if os.path.exists(marker):
        os.remove(marker)

def get_active_matches():
    """获取所有正在处理的 match"""
    ensure_dirs()
    active = []
    for f in os.listdir(MARKER_DIR):
        if f.endswith('.marker'):
            try:
                with open(os.path.join(MARKER_DIR, f), 'r') as fh:
                    info = json.load(fh)
                # 检查进程是否还活着
                try:
                    os.kill(info['pid'], 0)
                    active.append({
                        'match': f[:-7],  # 去掉 .marker
                        'pid': info['pid'],
                        'time': info['time'],
                        'session': info.get('session', 'unknown')
                    })
                except (ProcessLookupError, PermissionError):
                    pass  # 进程已死，保留标记
            except:
                pass
    return active

def get_running_scripts():
    """获取当前运行的竞彩相关脚本"""
    import subprocess
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-CimInstance Win32_Process -Filter "Name=\'python.exe\'" | '
             'Select-Object ProcessId,CommandLine | '
             'Where-Object { $_.CommandLine -match \'jingcai\' }'],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except:
        return ''

def list_locks():
    """列出所有锁"""
    ensure_dirs()
    locks = []
    for f in os.listdir(LOCK_DIR):
        if f.endswith('.pid'):
            name = f[:-4]
            pid_file = os.path.join(LOCK_DIR, f)
            try:
                with open(pid_file, 'r') as fh:
                    pid = int(fh.read().strip())
                try:
                    os.kill(pid, 0)
                    status = 'ACTIVE'
                except (ProcessLookupError, PermissionError):
                    status = 'STALE'
                locks.append({'name': name, 'pid': pid, 'status': status})
            except:
                locks.append({'name': name, 'pid': 'N/A', 'status': 'BROKEN'})
    return locks

def cleanup_stale_locks():
    """清理死锁"""
    ensure_dirs()
    removed = 0
    for f in os.listdir(LOCK_DIR):
        if not f.endswith('.pid'):
            continue
        pid_file = os.path.join(LOCK_DIR, f)
        try:
            with open(pid_file, 'r') as fh:
                pid = int(fh.read().strip())
            try:
                os.kill(pid, 0)
            except (ProcessLookupError, PermissionError):
                os.remove(pid_file)
                print(f'[LOCK] 清理死锁: {f[:-4]} (PID {pid})')
                removed += 1
        except:
            pass
    print(f'[LOCK] 清理完成: 移除 {removed} 个死锁')
    return removed

# 独立运行时的用法
if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print('工作区保护脚本')
        print()
        print('用法: python jingcai_lock.py [命令]')
        print()
        print('命令:')
        print('  list              列出所有锁')
        print('  clean             清理死锁')
        print('  active            列出正在处理的 match')
        print('  acquire <name>    获取锁')
        print('  release <name>    释放锁')
        sys.exit(0)
    
    cmd = args[0]
    if cmd == 'list':
        locks = list_locks()
        if not locks:
            print('无活跃锁')
        else:
            print(f'{"名称":<20} {"PID":>8} {"状态"}')
            print('-' * 40)
            for l in locks:
                print(f'{l["name"]:<20} {str(l["pid"]):>8} {l["status"]}')
    elif cmd == 'clean':
        cleanup_stale_locks()
    elif cmd == 'active':
        active = get_active_matches()
        if not active:
            print('无正在处理的 match')
        else:
            print(f'{"Match":<25} {"PID":>8} {"时间":<20} {"Session"}')
            print('-' * 80)
            for a in active:
                print(f'{a["match"]:<25} {str(a["pid"]):>8} {a["time"]:<20} {a["session"]}')
    elif cmd == 'acquire' and len(args) >= 2:
        if acquire_lock(args[1]):
            print('✓ 获取锁成功')
        else:
            print('✗ 获取锁失败 - 已有其他实例在运行')
            sys.exit(1)
    elif cmd == 'release' and len(args) >= 2:
        release_lock(args[1])
    else:
        print(f'未知命令: {cmd}')
        sys.exit(1)
