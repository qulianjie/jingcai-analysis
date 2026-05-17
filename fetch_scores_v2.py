# -*- coding: utf-8 -*-
"""从sporttery.cn获取比赛结果"""
import os, json, re, requests

BASE = os.path.join('jingcai', 'tasks')
all_metadatas = []

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            meta['_path'] = meta_path
            all_metadatas.append(meta)

print(f'总共 {len(all_metadatas)} 场')

# 方法1: 从500.com的tocai页面获取比分
updated = 0
score_map = {}

for meta in all_metadatas:
    if meta.get('score'):
        continue
    fid = meta.get('fid', '')
    matchnum = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    if not fid:
        continue
    
    # 尝试tocai页面
    urls = [
        f'https://info.500.com.cn/zqsb/{fid}.shtml',
        f'https://odds.500.com/fenxi/touzhu-{fid}.shtml',
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            content = resp.text
            
            # 找比分模式: X:X
            # 在tocai页面: score_val="3:1"
            m = re.search(r'score_val["\s:=]+"(\d+:\d+)"', content)
            if m:
                score = m.group(1)
                meta['score'] = score
                score_map[matchnum] = score
                with open(meta['_path'], 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                updated += 1
                print(f'  {matchnum} {home}vs{away}: {score} (from {url})')
                break
            
            # 在touzhu页面找比分
            m2 = re.search(r'(?:\d{2}:\d{2}[:\s]+)?(?:主队|客队).*?(\d)\s*[:：\-]\s*(\d)', content[:10000])
            if m2 and '竞彩' in content:
                score = f'{m2.group(1)}:{m2.group(2)}'
                meta['score'] = score
                score_map[matchnum] = score
                with open(meta['_path'], 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                updated += 1
                print(f'  {matchnum} {home}vs{away}: {score} (from {url} pattern2)')
                break
        except:
            pass

print(f'\n获取 {updated} 场比分')

# 打印所有
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
