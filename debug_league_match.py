# -*- coding: utf-8 -*-
"""
调试：查看多个match的源站联赛名和匹配情况
"""
import requests, json, os, re
from bs4 import BeautifulSoup

# 测试多个match
test_cases = [
    ('成功-0507-001', '2026-05-07', 'match1_莱切__乌迪内斯'),
    ('成功-0514-003', '2026-05-14', 'match3_比利亚雷__塞维利亚'),
    ('失败-0512-010', '2026-05-12', 'match10_赫塔费__马洛卡'),
    ('失败-0508-012', '2026-05-08', 'match12_莱万特__奥萨苏纳'),
]

def load_league_map():
    map_path = 'jingcai/league_map.json'
    builtin = {
        '韩职': ['K1联赛', 'K联赛'],
        '西甲': ['西甲'], '德甲': ['德甲'], '意甲': ['意甲'],
        '英超': ['英超'], '法甲': ['法甲'], '荷甲': ['荷甲'],
        '葡超': ['葡超'], '瑞超': ['瑞超', '瑞典超'],
        '挪超': ['挪超'], '丹超': ['丹超'], '比甲': ['比甲'],
        '土超': ['土超'], '俄超': ['俄超'], '巴甲': ['巴甲'],
        '阿甲': ['阿甲', '阿根甲'], '芬超': ['芬超', '芬兰'],
        '解放者杯': ['解放者杯', '南美解放者杯'],
        '欧冠': ['欧冠', '欧洲冠军联赛'],
        '欧联': ['欧联', '欧罗巴联赛', '欧罗巴'],
    }
    if os.path.exists(map_path):
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            builtin.update(data)
        except:
            pass
    return builtin

def league_match(src, target, m):
    if src == target:
        return True
    if not src or not target:
        return False
    if target in m and src in m[target]:
        return True
    if src in m and target in m[src]:
        return True
    if len(target) >= 2 and target in src:
        return True
    if len(src) >= 2 and src in target:
        return True
    return False

league_map = load_league_map()
sess = requests.Session()

results = []
for label, date, name in test_cases:
    meta_path = 'jingcai/tasks/%s/data/%s/meta.json' % (date, name)
    if not os.path.exists(meta_path):
        results.append('%s: meta.json not found' % label)
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    home_id = meta.get('home_id', '')
    league = meta.get('league', '')
    
    results.append('%s: 联赛="%s", home_id=%s' % (label, league, home_id))
    
    try:
        url = 'https://liansai.500.com/team/%s/teamfixture/' % home_id
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        src_leagues = set()
        match_count = 0
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                name_src = data.get('SIMPLEGBNAME', '')
                if name_src:
                    src_leagues.add(name_src)
                match_count += 1
            except:
                continue
        
        results.append('  比赛数: %d' % match_count)
        results.append('  源站联赛名: %s' % src_leagues)
        
        # 检查匹配
        matched = False
        for src in src_leagues:
            if league_match(src, league, league_map):
                results.append('  匹配: "%s" <-> "%s"' % (src, league))
                matched = True
        
        if not matched:
            results.append('  *** 不匹配! ***')
            results.append('  竞彩联赛: "%s"' % league)
            results.append('  源站联赛: %s' % src_leagues)
            results.append('  league_map[%s] = %s' % (league, league_map.get(league, 'NONE')))
    
    except Exception as e:
        results.append('  Error: %s' % str(e))
    
    results.append('')

with open('jingcai/league_match_debug.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
