#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 odds_europe.companies[] 提取竞彩 (官*) 和 IW (塞浦路斯) 数据，
补齐顶级字段 odds_europe.jc 和 odds_europe.iw。
修复巴甲/瑞超/挪超三个缓存。
"""

import json, os, sys, glob

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'league_cache')

# 竞彩公司名匹配：含'官'字（官*官*中国 / 竞*官*竞*官*中国）
# IW公司名匹配：含'塞浦路斯'（I**********I**********塞浦路斯）
JC_KEYWORDS = ['官']
IW_KEYWORD = '塞浦路斯'

def find_jc_company(companies):
    """找竞彩官方公司"""
    for c in companies:
        nm = c.get('name', '')
        if any(kw in nm for kw in JC_KEYWORDS) and c.get('iw') is not None:
            return c
    return None

def find_iw_company(companies):
    """找Interwetten公司（塞浦路斯）"""
    for c in companies:
        nm = c.get('name', '')
        if IW_KEYWORD in nm and c.get('iw') is not None:
            return c
    return None

def fix_file(filepath):
    name = os.path.basename(filepath)
    print(f'\n=== {name} ===')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    matches = cache.get('all_matches', [])
    total = len(matches)
    
    jc_fixed = 0; iw_fixed = 0
    
    for m in matches:
        oe = m.get('odds_europe')
        if not isinstance(oe, dict):
            continue
        
        companies = oe.get('companies', [])
        if not companies:
            continue
        
        # 补 odds_europe.jc（如果顶级字段缺失但companies里有）
        if not isinstance(oe.get('jc'), dict):
            jc_comp = find_jc_company(companies)
            if jc_comp:
                oe['jc'] = {
                    'iw': jc_comp['iw'], 'id': jc_comp['id'], 'il': jc_comp['il'],
                    'lw': jc_comp['lw'], 'ld': jc_comp['ld'], 'll': jc_comp['ll'],
                }
                # 如果有dir也带上
                if 'dir' in jc_comp:
                    oe['jc']['dir'] = jc_comp['dir']
                jc_fixed += 1
        
        # 补 odds_europe.iw（如果顶级字段缺失但companies里有）
        if not isinstance(oe.get('iw'), dict):
            iw_comp = find_iw_company(companies)
            if iw_comp:
                oe['iw'] = {
                    'iw': iw_comp['iw'], 'id': iw_comp['id'], 'il': iw_comp['il'],
                    'lw': iw_comp['lw'], 'ld': iw_comp['ld'], 'll': iw_comp['ll'],
                }
                if 'dir' in iw_comp:
                    oe['iw']['dir'] = iw_comp['dir']
                iw_fixed += 1
    
    # 写回
    cache['fix_date'] = cache.get('fix_date', '') + ' +fix_top_level_jc_iw'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    print(f'  补jc: {jc_fixed}/{total}  补iw: {iw_fixed}/{total}')

if __name__ == '__main__':
    targets = []
    if '--core' in sys.argv:
        # 全量扫描：所有顶级字段缺失但companies有的联赛
        for fn in os.listdir(CACHE_DIR):
            if not fn.endswith('.json'): continue
            fp = os.path.join(CACHE_DIR, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            matches = cache.get('all_matches', [])
            need_fix = False
            for m in matches[:20]:  # 抽检前20场
                oe = m.get('odds_europe')
                if not isinstance(oe, dict): continue
                if not isinstance(oe.get('jc'), dict) or not isinstance(oe.get('iw'), dict):
                    if oe.get('companies'):
                        need_fix = True
                        break
            if need_fix:
                targets.append(fp)
    else:
        # 指定文件名
        for fn in sys.argv[1:]:
            if not fn.endswith('.json'): fn += '.json'
            p = os.path.join(CACHE_DIR, fn) if not os.path.exists(fn) else fn
            if os.path.exists(p):
                targets.append(p)
            else:
                print(f'[SKIP] 不存在: {fn}')
    
    if not targets:
        print('用法: python3 fix_top_level_jc_iw.py 巴甲.json 瑞超.json')
        print('  或: python3 fix_top_level_jc_iw.py --core')
        sys.exit(1)
    
    for p in targets:
        fix_file(p)
    
    print('\n✅ 完成')
