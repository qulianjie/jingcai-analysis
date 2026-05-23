# -*- coding: utf-8 -*-
"""共享工具函数

当检查用：确保所有文件写入和输出使用utf-8编码。
"""
import os, re, sys, json, time

def ensure_utf8_stdout():
    """Ensure stdout uses UTF-8 encoding"""
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

def rd(path):
    """Read file content, return '' if not exists or empty"""
    if not os.path.exists(path):
        return ''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception:
        return ''

def re_find(text, pattern):
    """Regex find: return first capture group or None"""
    if not text:
        return None
    m = re.search(pattern, text)
    if m:
        return m.group(1)
    return None

def safe_json_load(path, default=None):
    """Load JSON file safely, return default on failure"""
    content = rd(path)
    if not content:
        return default
    try:
        return json.loads(content)
    except Exception:
        return default

def safe_json_dump(data, path, **kwargs):
    """Dump JSON to file safely"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, **kwargs)
    except Exception:
        pass

# URL templates for 500.com
TOUZHU_URL = 'https://odds.500.com/fenxi/touzhu-{fid}.shtml'
SCORE_URL = 'https://odds.500.com/fenxi/shuju-{fid}.shtml'

def load_matches_data(date_str, tasks_dir):
    """Load matches data for a given date"""
    # 优先 data/ 子目录，回退到父目录（pipeline组织文件后可能在data/下）
    data_dir = os.path.join(tasks_dir, date_str, 'data')
    matches_data_path = os.path.join(data_dir, 'matches_data.json')
    data = safe_json_load(matches_data_path, None)
    if data is not None:
        return data
    # 回退: 父目录匹配
    fallback = os.path.join(tasks_dir, date_str, 'matches_data.json')
    return safe_json_load(fallback, [])

def load_matches_list(tasks_dir):
    """Load matches list from a tasks directory"""
    data = safe_json_load(os.path.join(tasks_dir, 'matches_list.json'))
    return data if data else []
