# -*- coding: utf-8 -*-
"""从sporttery.cn获取竞彩比赛结果"""
import os, json, re, requests, time
from collections import defaultdict

BASE = os.path.join('jingcai', 'tasks')

# 收集所有meta
all_metadatas = []
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        meta['_path'] = meta_path
        meta['_date'] = d
        all_metadatas.append(meta)

# 按日期分组
dates = defaultdict(list)
for m in all_metadatas:
    dates[m['_date']].append(m)

print(f'共 {len(all_metadatas)}场，{len(dates)}个日期')

# 方法1: 从sporttery.cn获取
def fetch_sporttery_results(date_str):
    """从sporttery.cn获取竞彩比赛结果"""
    # sporttery.cn jcxmapl interface
    url = f'https://info.sporttery.cn/football/match_result.php?dt={date_str.replace("-", "")}'
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.encoding = 'utf-8'
        return resp.text
    except:
        return None

# 方法2: 从500.com比分中心获取
def fetch_500_scores(date_str):
    """从500.com比分中心获取"""
    url = f'https://odds.500.com/fzc/{date_str.replace("-", "")}.shtml'
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }, timeout=10)
        resp.encoding = 'utf-8'
        return resp.text
    except:
        return None

updated = 0

# 先尝试从500.com比分中心
for date_str in sorted(dates.keys()):
    matches = dates[date_str]
    if not matches:
        continue
    
    # 获取500.com比分页面
    ymd = date_str.replace('-', '')
    url = f'https://odds.500.com/fzc/{ymd}.shtml'
    
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }, timeout=10)
        resp.encoding = 'utf-8'
        content = resp.text
        
        # 找竞彩比赛结果
        # 500.com比分页面格式: 包含竞彩编号和比分
        # 匹配: 竞彩编号 + 比分
        score_pattern = re.findall(r'([一二三四五六日])\s*(\d{3})[^<]*?(\d+)[\s:：\-]+(\d+)', content)
        
        for p in score_pattern:
            weekday = p[0]
            num = p[1]
            home_score = p[2]
            away_score = p[3]
            matchnum = f'周{weekday}{num}'
            
            for m in matches:
                if m.get('matchnum', '') == matchnum:
                    m['score'] = f'{home_score}:{away_score}'
                    with open(m['_path'], 'w', encoding='utf-8') as f:
                        json.dump(m, f, ensure_ascii=False, indent=2)
                    updated += 1
                    print(f'  {matchnum} {m.get("home","")}vs{m.get("away","")}: {home_score}:{away_score}')
        
        time.sleep(0.2)
    except Exception as e:
        print(f'  {date_str}: 获取失败 - {str(e)[:50]}')

print(f'\n获取 {updated} 场比分')

# 打印所有比分
print('\n所有比分:')
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            score = meta.get('score', '')
            matchnum = meta.get('matchnum', '')
            if score and matchnum:
                print(f'  {matchnum}: {score}')
