# -*- coding: utf-8 -*-
"""
从500.com获取竞彩足球开奖结果（支持历史日期）
"""
import os, json, re, requests
from datetime import datetime, timedelta

def fetch_scores_from_500():
    """从500.com获取开奖结果"""
    url = 'https://trade.500.com/jcgc/'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://trade.500.com/'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        scores = {}
        matchnum_pattern = re.compile(r'(周[一二三四五六日]\d+)')
        score_pattern = re.compile(r'(\d+)[：:](\d+)')
        
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
        
        for row in rows:
            num_match = matchnum_pattern.search(row)
            if not num_match:
                continue
            matchnum = num_match.group(1)
            
            score_match = score_pattern.search(row)
            if not score_match:
                continue
            
            home = int(score_match.group(1))
            away = int(score_match.group(2))
            scores[matchnum] = f'{home}:{away}'
        
        return scores
    
    except Exception as e:
        print(f'获取失败: {e}')
        return {}

def main():
    print('从500.com获取比分...')
    scores = fetch_scores_from_500()
    print(f'获取到 {len(scores)}场比分')
    
    for k, v in sorted(scores.items()):
        print(f'  {k}: {v}')
    
    # 写入meta.json
    BASE = os.path.join('jingcai', 'tasks')
    updated = 0
    
    for d in sorted(os.listdir(BASE)):
        dp = os.path.join(BASE, d)
        if not os.path.isdir(dp):
            continue
        data_dir = os.path.join(dp, 'data')
        if not os.path.isdir(data_dir):
            continue
        
        for m_name in sorted(os.listdir(data_dir)):
            m_path = os.path.join(data_dir, m_name)
            if not (os.path.isdir(m_path) and m_name.startswith('match')):
                continue
            
            meta_path = os.path.join(m_path, 'meta.json')
            if not os.path.exists(meta_path):
                continue
            
            try:
                meta = json.load(open(meta_path, 'r', encoding='utf-8'))
                matchnum = meta.get('matchnum', '')
                
                if matchnum in scores:
                    meta['score'] = scores[matchnum]
                    json.dump(meta, open(meta_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                    updated += 1
            except:
                pass
    
    print(f'\n总更新: {updated}场')

if __name__ == '__main__':
    main()
