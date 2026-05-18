# -*- coding: utf-8 -*-
"""
竞彩工具模块 - 统一公共函数
所有核心脚本应从此模块 import 公共函数，避免重复代码。

包含：
1. rd() 安全读文件
2. re_find() / re_find_int() 正则提取
3. ensure_utf8_stdout() Windows 编码修复
4. safe_json_load() 安全加载 JSON
5. setup_logger() 日志设置（从 _log_util 转发）
"""

import os
import json
import sys
import re
import io

from _log_util import setup_logger


def ensure_utf8_stdout():
    """修复 Windows 控制台 UTF-8 编码输出"""
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass
    try:
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


def rd(path):
    """安全读文件，返回字符串。文件不存在或异常时返回空字符串"""
    if not os.path.exists(path):
        return ''
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return ''


def re_find(text, pattern, group=1, default=''):
    """正则查找，返回指定分组。未找到时返回 default"""
    if not text:
        return default
    try:
        m = re.search(pattern, text)
        if m:
            return m.group(group)
    except:
        pass
    return default


def re_find_int(text, pattern, group=1, default=0):
    """正则查找并转 int"""
    val = re_find(text, pattern, group)
    if val and val.strip():
        try:
            return int(val.strip())
        except:
            pass
    return default


def re_find_float(text, pattern, group=1, default=0.0):
    """正则查找并转 float"""
    val = re_find(text, pattern, group)
    if val and val.strip():
        try:
            return float(val.strip())
        except:
            pass
    return default


def safe_json_load(path, default=None):
    """安全加载 JSON 文件，异常时返回 default"""
    if default is None:
        default = {}
    try:
        content = rd(path)
        if content:
            return json.loads(content)
    except:
        pass
    return default


def safe_json_dump(data, path, **kwargs):
    """安全写入 JSON 文件"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, **kwargs)
        return True
    except Exception as e:
        return False


def find_file_in_date(match_dir, date_dir, filename):
    """在 match 目录和 date data/子目录中查找文件"""
    # 直接路径
    fp = os.path.join(match_dir, filename)
    if os.path.exists(fp):
        return fp
    
    # date data 下的 match* 子目录
    if date_dir:
        data_dir = os.path.join(os.path.dirname(match_dir), 'data')
        if os.path.exists(data_dir):
            for sub in os.listdir(data_dir):
                sub_path = os.path.join(data_dir, sub)
                if os.path.isdir(sub_path):
                    candidate = os.path.join(sub_path, filename)
                    if os.path.exists(candidate):
                        return candidate
    return ''


# ============ URL 常量 ============
TOUZHU_URL = 'https://odds.500.com/fenxi/touzhu-{fid}.shtml'
SCORE_URL = 'https://odds.500.com/fenxi/czgb-{fid}.shtml'

# ============ 数据加载函数 ============
def load_matches_data(date_str, tasks_dir):
    """从 matches_data.json 加载比赛 fid 映射"""
    if not tasks_dir:
        tasks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')
    
    # 优先找 tasks/{date}/matches_data.json，其次 tasks/{date}/data/matches_data.json
    data_file = os.path.join(tasks_dir, date_str, 'matches_data.json')
    if not os.path.exists(data_file):
        data_file = os.path.join(tasks_dir, date_str, 'data', 'matches_data.json')
    if not os.path.exists(data_file):
        return {}
    
    with open(data_file, 'rb') as f:
        raw = f.read().decode('utf-8')
    
    try:
        data = json.loads(raw)
        fid_map = {}
        for group_key in data.get('groups', {}):
            group = data['groups'][group_key]
            for m in group.get('matches', []):
                num = m.get('matchnum', '')
                fid = m.get('fid', '')
                if num and fid:
                    fid_map[num] = fid
        return fid_map
    except:
        return {}


def load_matches_list(date_str, tasks_dir):
    """从 matches_data.json 加载比赛列表（含完整信息）"""
    if not tasks_dir:
        tasks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')
    
    data_file = os.path.join(tasks_dir, date_str, 'matches_data.json')
    if not os.path.exists(data_file):
        data_file = os.path.join(tasks_dir, date_str, 'data', 'matches_data.json')
    if not os.path.exists(data_file):
        return []
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_matches = []
        for group_name, group_data in data.get('groups', {}).items():
            if isinstance(group_data, dict) and 'matches' in group_data:
                for m in group_data['matches']:
                    all_matches.append(m)
        return all_matches
    except:
        return []


if __name__ == '__main__':
    print('竞彩工具模块 _util.py')
    print('    函数列表:')
    print('    ensure_utf8_stdout()')
    print('    rd(), re_find(), re_find_int(), re_find_float()')
    print('    safe_json_load(), safe_json_dump()')
    print('    find_file_in_date()')
    print('    setup_logger() (从 _log_util 转发)')
    print('    TOUZHU_URL, SCORE_URL 常量')
    print('    load_matches_data(), load_matches_list()')
