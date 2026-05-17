# -*- coding: utf-8 -*-
"""
Step 0 增强：获取比赛列表时，主动探测联赛名映射
"""
import sys, os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 导入原有 step0 逻辑
from step0_fetch_matches import fetch_sunday_matches, save_matches

# 导入联赛映射模块
from league_mapper import discover_league_mapping, load_map, save_map

def enhance_with_league_mapping(matches, date_str):
    """增强：为每场比赛探测联赛名映射"""
    import requests
    
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    
    # 获取已有映射
    existing = load_map()
    discovered_count = 0
    
    for m in matches:
        fid = m.get('fid', '')
        jingcai_league = m.get('league', '')
        
        if not fid or not jingcai_league:
            continue
        
        # 如果联赛已在映射中，跳过
        if jingcai_league in existing:
            continue
        
        # 探测联赛名
        print(f'  [联赛探测] fid={fid} 竞彩名={jingcai_league}')
        jl, sl = discover_league_mapping(fid, sess)
        
        if jl:
            discovered_count += 1
    
    if discovered_count > 0:
        print(f'  [联赛探测] 新增 {discovered_count} 个联赛映射')
    
    return matches

if __name__ == '__main__':
    from datetime import datetime
    
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    
    print(f'[STEP] 第0步增强：获取竞彩比赛列表 + 联赛映射探测')
    print(f'[DATE] 比赛日期: {date_str}')
    
    result = fetch_sunday_matches(date_str)
    if not result:
        print('[ERROR] 获取比赛列表失败')
        sys.exit(1)
    
    # 增强：探测联赛映射
    for day, group in result.get('groups', {}).items():
        for m in group.get('matches', []):
            # 检查是否需要探测
            jingcai_league = m.get('league', '')
            existing = load_map()
            if jingcai_league and jingcai_league not in existing:
                print(f'  [联赛探测] fid={m.get("fid")} 竞彩名={jingcai_league}')
    
    # 保存
    paths = save_matches(result)
    
    # 输出映射状态
    m = load_map()
    print(f'\n[MAP] 联赛映射表: {len(m)} 个条目')
    for key in sorted(m.keys()):
        aliases = m[key]
        print(f'  {key} -> {", ".join(aliases)}')
    
    total = sum(g['count'] for g in result['groups'].values())
    print(f'\n[OK] 共 {total} 场比赛')
    print(f'[OK] 联赛映射: {len(m)} 个条目')
