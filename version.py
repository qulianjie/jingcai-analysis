# -*- coding: utf-8 -*-
"""
竞彩工作区版本管理工具
用法: python jingcai/version.py [命令]
命令:
  init              初始化版本管理（创建 base 版本）
  snapshot [name]   创建快照
  list              列出所有版本
  diff <name>       比较版本差异
  restore <name>    恢复到指定版本
  status            显示版本状态
"""
import os, sys, json, shutil, hashlib
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
VERSIONS_DIR = os.path.join(WORKSPACE, 'versions')
MANIFEST_FILE = os.path.join(VERSIONS_DIR, 'manifest.json')

# 竞彩流程脚本列表（需要版本管理的核心脚本）
JINGCAI_SCRIPTS = [
    'step0_fetch_matches.py',
    'step146_extractor.py',
    'step235_runner.py',
    'step7_runner.py',
    'step8_1923_extractor.py',
    'step918_extractor.py',
    'step24_extractor.py',
    'final_report_generator.py',
    'run_pipeline.py',
    'batch_full.py',
    'protect.py',
    'jingcai_feedback.py',
    'jingcai_feedback_v2.py',
    'batch_feedback.py',
]

# 小红书流程脚本列表
XHS_SCRIPTS = [
    'daily_generate_v8.py',
]

# 兼容旧名
PIPELINE_SCRIPTS = JINGCAI_SCRIPTS

def ensure_versions_dir():
    os.makedirs(VERSIONS_DIR, exist_ok=True)

def _script_hash(script_path):
    """计算脚本文件的哈希值"""
    try:
        with open(script_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return 'missing'

def _load_manifest():
    """加载版本清单"""
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'version': 1, 'snapshots': []}

def _save_manifest(manifest):
    """保存版本清单"""
    ensure_versions_dir()
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def _snapshot_dir(name):
    """获取快照目录"""
    return os.path.join(VERSIONS_DIR, name)

def init_base():
    """初始化 base 版本（当前正在使用的版本）"""
    ensure_versions_dir()
    base_dir = _snapshot_dir('base')
    os.makedirs(base_dir, exist_ok=True)
    
    manifest = _load_manifest()
    base_info = {
        'name': 'base',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'base',
        'description': '当前在用版本（base）',
        'scripts': {}
    }
    
    copied = 0
    # 竞彩脚本
    for script in JINGCAI_SCRIPTS:
        src = os.path.join(WORKSPACE, script)
        dst = os.path.join(base_dir, script)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            base_info['scripts']['jingcai/' + script] = {
                'hash': _script_hash(src),
                'size': os.path.getsize(src)
            }
            copied += 1
            print('[version] 备份: jingcai/%s' % script)
    
    # 小红书脚本
    xhs_dir = os.path.join(os.path.dirname(WORKSPACE), '自媒体', 'scripts')
    for script in XHS_SCRIPTS:
        src = os.path.join(xhs_dir, script)
        dst = os.path.join(base_dir, 'xhs_' + script)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            base_info['scripts']['xhs/' + script] = {
                'hash': _script_hash(src),
                'size': os.path.getsize(src)
            }
            copied += 1
            print('[version] 备份: xhs/%s' % script)
    
    manifest['snapshots'].append(base_info)
    _save_manifest(manifest)
    print('[version] OK base 版本已创建 (%d 个脚本)' % copied)
    return copied

def snapshot(name=None):
    """创建快照"""
    ensure_versions_dir()
    if not name:
        name = datetime.now().strftime('snap_%Y%m%d_%H%M%S')
    
    snap_dir = _snapshot_dir(name)
    if os.path.exists(snap_dir):
        print('[version] 快照 %s 已存在' % name)
        return False
    
    os.makedirs(snap_dir)
    manifest = _load_manifest()
    snap_info = {
        'name': name,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'snapshot',
        'description': '',
        'scripts': {}
    }
    
    copied = 0
    # 竞彩脚本
    for script in JINGCAI_SCRIPTS:
        src = os.path.join(WORKSPACE, script)
        dst = os.path.join(snap_dir, script)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            snap_info['scripts']['jingcai/' + script] = {
                'hash': _script_hash(src),
                'size': os.path.getsize(src)
            }
            copied += 1
            print('[version] 备份: jingcai/%s' % script)
    
    # 小红书脚本
    xhs_dir = os.path.join(os.path.dirname(WORKSPACE), '自媒体', 'scripts')
    for script in XHS_SCRIPTS:
        src = os.path.join(xhs_dir, script)
        dst = os.path.join(snap_dir, 'xhs_' + script)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            snap_info['scripts']['xhs/' + script] = {
                'hash': _script_hash(src),
                'size': os.path.getsize(src)
            }
            copied += 1
            print('[version] 备份: xhs/%s' % script)
    
    manifest['snapshots'].append(snap_info)
    _save_manifest(manifest)
    print('[version] OK 快照 %s 已创建 (%d 个脚本)' % (name, copied))
    return True

def list_versions():
    """列出所有版本"""
    manifest = _load_manifest()
    if not manifest['snapshots']:
        print('[version] 无版本记录')
        return
    
    print('[version] 版本列表 (%d):' % len(manifest['snapshots']))
    print('  %-25s %-20s %-10s %s' % ('名称', '时间', '类型', '描述'))
    print('  ' + '-' * 70)
    for s in manifest['snapshots']:
        print('  %-25s %-20s %-10s %s' % (
            s['name'],
            s['time'],
            s.get('type', '?'),
            s.get('description', '')
        ))

def diff(name):
    """比较版本差异"""
    snap_dir = _snapshot_dir(name)
    if not os.path.exists(snap_dir):
        print('[version] 快照 %s 不存在' % name)
        return
    
    print('[version] 比较 %s 与当前:' % name)
    manifest = _load_manifest()
    snap_info = None
    for s in manifest['snapshots']:
        if s['name'] == name:
            snap_info = s
            break
    
    if not snap_info:
        print('[version] 快照信息不存在')
        return
    
    changed = 0
    for script_key, info in snap_info['scripts'].items():
        # 解析脚本路径
        if script_key.startswith('xhs/'):
            xhs_dir = os.path.join(os.path.dirname(WORKSPACE), '自媒体', 'scripts')
            script_name = script_key[4:]  # 去掉 'xhs/'
            current_hash = _script_hash(os.path.join(xhs_dir, script_name))
        else:
            current_hash = _script_hash(os.path.join(WORKSPACE, script_key))
        
        if current_hash != info['hash']:
            print('  [MODIFIED] %s' % script_key)
            changed += 1
        else:
            print('  [SAME]     %s' % script_key)
    
    print('[version] 差异: %d 个脚本已修改' % changed)

def restore(name):
    """恢复到指定版本"""
    snap_dir = _snapshot_dir(name)
    if not os.path.exists(snap_dir):
        print('[version] 快照 %s 不存在' % name)
        return False
    
    manifest = _load_manifest()
    snap_info = None
    for s in manifest['snapshots']:
        if s['name'] == name:
            snap_info = s
            break
    
    if not snap_info:
        print('[version] 快照信息不存在')
        return False
    
    # 先备份当前版本
    print('[version] 先备份当前版本...')
    init_base()
    
    # 恢复
    restored = 0
    for script_key in snap_info['scripts']:
        if script_key.startswith('xhs/'):
            xhs_dir = os.path.join(os.path.dirname(WORKSPACE), '自媒体', 'scripts')
            script_name = script_key[4:]
            src = os.path.join(snap_dir, 'xhs_' + script_name)
            dst = os.path.join(xhs_dir, script_name)
        else:
            src = os.path.join(snap_dir, script_key)
            dst = os.path.join(WORKSPACE, script_key)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print('[version] 恢复: %s' % script_key)
            restored += 1
    
    print('[version] OK 已恢复到 %s (%d 个脚本)' % (name, restored))
    return True

def status():
    """显示版本状态"""
    manifest = _load_manifest()
    print('[version] 版本状态:')
    print('  快照数: %d' % len(manifest['snapshots']))
    
    for s in manifest['snapshots']:
        print('\n  [%s] %s' % (s.get('type', '?'), s['name']))
        print('  时间: %s' % s['time'])
        print('  描述: %s' % s.get('description', ''))
        print('  脚本数: %d' % len(s.get('scripts', {})))
        
        # 检查当前文件是否与快照一致
        current_changed = 0
        for script_key, info in s.get('scripts', {}).items():
            if script_key.startswith('xhs/'):
                xhs_dir = os.path.join(os.path.dirname(WORKSPACE), '自媒体', 'scripts')
                script_name = script_key[4:]
                current_hash = _script_hash(os.path.join(xhs_dir, script_name))
            else:
                current_hash = _script_hash(os.path.join(WORKSPACE, script_key))
            if current_hash != info['hash']:
                current_changed += 1
        if current_changed > 0:
            print('  当前差异: %d 个脚本已修改' % current_changed)
        else:
            print('  当前状态: 与快照一致')

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print('竞彩工作区版本管理工具')
        print()
        print('用法: python jingcai/version.py [命令]')
        print()
        print('命令:')
        print('  init              初始化 base 版本')
        print('  snapshot [name]   创建快照')
        print('  list              列出所有版本')
        print('  diff <name>       比较版本差异')
        print('  restore <name>    恢复到指定版本')
        print('  status            显示版本状态')
        sys.exit(0)
    
    cmd = args[0]
    if cmd == 'init':
        init_base()
    elif cmd == 'snapshot':
        name = args[1] if len(args) > 1 else None
        snapshot(name)
    elif cmd == 'list':
        list_versions()
    elif cmd == 'diff' and len(args) >= 2:
        diff(args[1])
    elif cmd == 'restore' and len(args) >= 2:
        restore(args[1])
    elif cmd == 'status':
        status()
    else:
        print('[version] 未知命令: %s' % cmd)
        sys.exit(1)
