#!/usr/bin/env python3
"""从500.com亚盘页正则提取澳门盘口，写meta.json的macau_line"""
import sys, os, json, re
import requests

if len(sys.argv) < 2:
    print('用法: python _sync_macau_line.py <match_dir>')
    sys.exit(1)

match_dir = sys.argv[1]
meta_path = os.path.join(match_dir, 'meta.json')
if not os.path.exists(meta_path):
    print('meta.json 不存在'); sys.exit(1)

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

fid = meta.get('fid', '')
if not fid:
    print('meta中无fid'); sys.exit(1)

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0'})
try:
    r = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % fid, timeout=15)
    r.encoding = 'gbk'
    text = r.text
except Exception as e:
    print('获取页面失败:', e); sys.exit(1)

raw = text.encode('gbk', errors='replace')
m = re.search(rb'cid=5.*?quancheng.*?</span>.*?pl_table_data[^>]*>.*?<tr[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>[^<]*</td>', raw, re.DOTALL)
if m:
    cp = m.group(1).decode('gbk', errors='replace').strip()
    cp = re.sub(r'<[^>]+>', '', cp).strip()
    if cp:
        meta['macau_line'] = cp
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print('macau_line:', cp)
        # 验证回读
        with open(meta_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        print('verified:', d['macau_line'])
        sys.exit(0)

print('未找到澳门盘口')
sys.exit(1)
