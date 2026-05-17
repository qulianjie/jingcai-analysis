# -*- coding: utf-8 -*-
"""用多种方式获取比分"""
import os, json, re, requests, time

BASE = os.path.join('jingcai', 'tasks')
score_map = {}

# 方法1: 从500.com toc ai 接口
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    date_updated = 0
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        if meta.get('score'):
            continue
        
        fid = meta.get('fid', '')
        matchnum = meta.get('matchnum', '')
        home = meta.get('home', '')
        away = meta.get('away', '')
        
        if not fid:
            continue
        
        # 方法: 500.com toc ai 页
        try:
            url = f'https://info.500.com.cn/zqsb/{fid}.shtml'
            resp = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://info.500.com.cn/',
            }, timeout=10)
            resp.encoding = 'gbk'
            
            # 找比分
            # 页面结构: score_val="X:X" 或 比分 X:X
            m_score = re.search(r'score_val["\s:=]+"(\d+:\d+)"', resp.text)
            if not m_score:
                m_score = re.search(r'(\d+)\s*[:：]\s*(\d+)', resp.text)
            
            if m_score:
                score = m_score.group(1)
                if ':' not in score:
                    score = f'{m_score.group(1)}:{m_score.group(2)}'
                parts = score.split(':')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    meta['score'] = score
                    score_map[f'{matchnum}'] = score
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                    date_updated += 1
                    print(f'  {matchnum} {home}vs{away}: {score}')
        except:
            pass
    
    if date_updated > 0:
        print(f'  {d}: {date_updated}场')

print(f'\n共获取 {len(score_map)} 场比分')
