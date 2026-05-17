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

updated = 0

# 方法: sporttery.cn 比赛结果API
# URL: https://www.sporttery.cn/jc/zq/match_result/ajax_list.php?date=20260503
for date_str in sorted(dates.keys()):
    matches = dates[date_str]
    ymd = date_str.replace('-', '')
    
    url = f'https://www.sporttery.cn/jc/zq/match_result/ajax_list.php?date={ymd}'
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': f'https://www.sporttery.cn/jc/zq/match_result.php?date={ymd}',
        }, timeout=10)
        resp.encoding = 'utf-8'
        
        # 返回JSON格式: {"match_list":[...]}
        data = json.loads(resp.text)
        match_list = data.get('match_list', [])
        
        for item in match_list:
            match_num = item.get('match_num', '')  # 如 "001"
            home_name = item.get('home_name', '')
            away_name = item.get('away_name', '')
            score = item.get('score', '')  # 如 "2:1"
            match_date = item.get('match_date', '')
            
            # 找星期几
            weekday_map = {'周一': '一', '周二': '二', '周三': '三', '周四': '四', '周五': '五', '周六': '六', '周日': '日'}
            for wd, ch in weekday_map.items():
                if date_str in wd or ymd in date_str:
                    # 构造matchnum
                    matchnum = f'周{ch}{match_num.zfill(3)}'
                    break
            
            # 匹配meta
            for m in matches:
                meta_matchnum = m.get('matchnum', '')
                meta_home = m.get('home', '')
                meta_away = m.get('away', '')
                
                if meta_matchnum == matchnum or (meta_home in home_name and meta_away in away_name and score):
                    if score and ':' in score:
                        m['score'] = score
                        with open(m['_path'], 'w', encoding='utf-8') as f:
                            json.dump(m, f, ensure_ascii=False, indent=2)
                        updated += 1
                        print(f'  {meta_matchnum} {meta_home}vs{meta_away}: {score}')
        
        time.sleep(0.3)
    except Exception as e:
        print(f'  {date_str}: {str(e)[:80]}')

print(f'\n获取 {updated} 场比分')
