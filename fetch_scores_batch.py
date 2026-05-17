# -*- coding: utf-8 -*-
"""
从sporttery.cn获取竞彩足球开奖结果
"""
import os, json, re, requests
from datetime import datetime, timedelta

def fetch_scores_from_sporttery():
    """从体彩官网获取开奖结果"""
    url = 'https://www.sporttery.cn/jc/jszq/jczqxq/jcqfjj.html'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.sporttery.cn/'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        # 解析开奖结果表格
        # 查找包含比分的行
        score_pattern = re.compile(r'(\d+)[：:](\d+)')
        matchnum_pattern = re.compile(r'(周[一二三四五六日]\d+)')
        
        scores = {}
        # 简化解析：直接搜索包含比分的tr
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
        
        for row in rows:
            # 提取竞彩编号
            num_match = matchnum_pattern.search(row)
            if not num_match:
                continue
            matchnum = num_match.group(1)
            
            # 提取比分
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

def fetch_scores_from_500com():
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
    print('从sporttery.cn获取比分...')
    scores1 = fetch_scores_from_sporttery()
    print(f'sporttery: {len(scores1)}场')
    
    print('\n从500.com获取比分...')
    scores2 = fetch_scores_from_500com()
    print(f'500.com: {len(scores2)}场')
    
    # 合并
    all_scores = {}
    all_scores.update(scores1)
    all_scores.update(scores2)
    
    print(f'\n总唯一比分: {len(all_scores)}场')
    for k, v in sorted(all_scores.items()):
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
                
                if matchnum in all_scores:
                    meta['score'] = all_scores[matchnum]
                    json.dump(meta, open(meta_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                    updated += 1
            except:
                pass
    
    print(f'\n总更新: {updated}场')

if __name__ == '__main__':
    main()
