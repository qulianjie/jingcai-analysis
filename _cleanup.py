# -*- coding: utf-8 -*-
"""
定时清理脚本 - 定期清理中间数据，只保留最终报告和比分存档

用法:
    python jingcai/_cleanup.py                    # 默认：清理30天前的中间数据
    python jingcai/_cleanup.py --days 15           # 清理15天前的
    python jingcai/_cleanup.py --dry-run           # 只列出不删除
    python jingcai/_cleanup.py --help              # 帮助
"""

import os
import shutil
import sys
from datetime import datetime, timedelta

TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')
DATA_DIR = os.path.join(os.path.dirname(TASKS_DIR), 'data', 'jingcai')

# 保留文件类型（最终报告 + meta.json）
KEEP_FILES = {
    '.md',            # 最终报告
    'meta.json',      # 比赛元数据
}

# 保留的数据目录（不删）
KEEP_DATA_SUBDIRS = {
    '.md',
}

def parse_date_dir(dirname):
    """解析日期格式目录名，返回 datetime 对象"""
    try:
        return datetime.strptime(dirname, '%Y-%m-%d')
    except:
        return None

def get_days_old(dir_date, cutoff_days):
    """判断目录是否超过 cutoff_days 天"""
    return (datetime.now() - dir_date).days > cutoff_days

def clean_task_dir(task_dir, cutoff_days, dry_run=False):
    """清理单个日期目录"""
    date_name = os.path.basename(task_dir)
    date_obj = parse_date_dir(date_name)
    if not date_obj:
        return 0
    
    if not get_days_old(date_obj, cutoff_days):
        return 0
    
    total_size = 0
    removed = 0
    
    # 保留 .md 报告 + meta.json，删 data/ 子目录
    data_subdir = os.path.join(task_dir, 'data')
    if os.path.isdir(data_subdir):
        for item in os.listdir(data_subdir):
            item_path = os.path.join(data_subdir, item)
            total_size += get_dir_size(item_path)
            
            if dry_run:
                print(f'  [DRY-RUN] 将被删除: {item_path}')
                removed += 1
            else:
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    removed += 1
                except Exception as e:
                    print(f'  ⚠️ 删除失败 {item_path}: {e}')
    
    # 删 logs/
    logs_dir = os.path.join(task_dir, 'logs')
    if os.path.isdir(logs_dir):
        total_size += get_dir_size(logs_dir)
        if dry_run:
            print(f'  [DRY-RUN] 将被删除: {logs_dir}')
        else:
            try:
                shutil.rmtree(logs_dir)
            except:
                pass
    
    total_mb = total_size / (1024 * 1024)
    if not dry_run and removed > 0:
        print(f'  {date_name}: 清理了 {removed} 项 ({total_mb:.1f} MB)')
    
    return removed

def get_dir_size(path):
    """获取目录总大小"""
    total = 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total

def main():
    # 解析参数
    cutoff_days = 30
    dry_run = False
    
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    
    for i, a in enumerate(sys.argv[1:]):
        if a == '--days' and i + 2 < len(sys.argv):
            try:
                cutoff_days = int(sys.argv[i + 2])
            except:
                pass
        elif a == '--dry-run':
            dry_run = True
        elif a == '--help':
            print(__doc__)
            return
    
    if not os.path.isdir(TASKS_DIR):
        print(f'⚠️ tasks 目录不存在: {TASKS_DIR}')
        return
    
    # 计算各日期目录的占用
    total_before = get_dir_size(TASKS_DIR)
    total_removed = 0
    
    print(f'{">"*40}')
    print(f'中间数据清理（保留 {cutoff_days} 天内的完整数据）')
    if dry_run:
        print(f'[DRY-RUN 模式] 只列出不删除')
    print(f'{">"*40}')
    print()
    
    for task_dir in sorted(os.listdir(TASKS_DIR)):
        full_path = os.path.join(TASKS_DIR, task_dir)
        if not os.path.isdir(full_path):
            continue
        clean_task_dir(full_path, cutoff_days, dry_run)
    
    if not dry_run:
        total_after = get_dir_size(TASKS_DIR)
        saved_mb = (total_before - total_after) / (1024 * 1024)
        remaining_mb = total_after / (1024 * 1024)
        print(f'\n清理前: {total_before/(1024*1024):.1f} MB')
        print(f'清理后: {remaining_mb:.1f} MB')
        print(f'释放: {saved_mb:.1f} MB')

if __name__ == '__main__':
    main()
