# -*- coding: utf-8 -*-
"""从 leagues_all.json 生成完整的 league_map.json"""
import json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALL_FILE = os.path.join(SCRIPT_DIR, 'leagues_all.json')
MAP_FILE = os.path.join(SCRIPT_DIR, 'league_map.json')

# 竞彩常用简称 → 源站关键词（从竞彩官网近30天465场比赛实际提取的31个联赛）
ABBREV = {
    # 五大联赛
    '英超': ['英超', '英格兰超级联赛'],
    '西甲': ['西甲', '西班牙甲级联赛'],
    '德甲': ['德甲', '德国甲级联赛'],
    '意甲': ['意甲', '意大利甲级联赛'],
    '法甲': ['法甲', '法国甲级联赛'],
    # 二级联赛
    '英冠': ['英冠', '英格兰冠军联赛'],
    '德乙': ['德乙', '德国乙级联赛'],
    '法乙': ['法乙', '法国乙级联赛'],
    # 其他联赛
    '荷甲': ['荷甲', '荷兰甲级联赛', '荷兰超级联赛'],
    '荷乙': ['荷乙', '荷兰乙级联赛'],
    '葡超': ['葡超', '葡萄牙超级联赛'],
    '瑞超': ['瑞超', '瑞典超级联赛'],
    '挪超': ['挪超', '挪威超级联赛'],
    '韩职': ['韩职', '韩国经典K联赛', 'K1联赛', 'K联赛'],
    '日职': ['日职', '日本甲级联赛', 'J1联赛', 'J1'],
    '澳超': ['澳超', '澳大利亚超级联赛'],
    '美职足': ['美职足', '美国职业大联盟', '美职联'],
    '沙特职业联赛': ['沙特职业联赛', '沙特', '沙特联'],
    '芬兰超级联赛': ['芬兰超级联赛', '芬超'],
    # 洲际赛事
    '欧冠': ['欧冠', '欧洲冠军联赛'],
    '欧罗巴': ['欧罗巴', '欧联', '欧罗巴联赛'],
    '欧协联': ['欧协联', '欧洲协会联赛'],
    '解放者杯': ['解放者杯', '南美解放者杯'],
    '亚冠': ['亚冠', '亚洲冠军联赛'],
    '亚洲冠军乙级联赛': ['亚洲冠军乙级联赛', '亚冠2'],
    # 杯赛
    '英足总杯': ['英足总杯', '英格兰足总杯', '足总杯'],
    '德国杯': ['德国杯'],
    '意大利杯': ['意大利杯'],
    '法国杯': ['法国杯'],
    '国王杯': ['国王杯', '西班牙国王杯'],
    '荷兰杯': ['荷兰杯'],
}

with open(ALL_FILE, 'r', encoding='utf-8') as f:
    all_leagues = json.load(f)

print(f'总联赛数: {len(all_leagues)}')

# 构建映射
league_map = {}

# 1. 竞彩简称 → 源站名列表
for abbr, keywords in ABBREV.items():
    sources = []
    for l in all_leagues:
        name = l['name']
        for kw in keywords:
            if kw in name or name in kw:
                sources.append(name)
                break
    if sources:
        league_map[abbr] = list(set(sources))

# 2. 源站全称 → 自身 + 竞彩简称
for l in all_leagues:
    name = l['name']
    aliases = [name]
    # 找对应的竞彩简称
    for abbr, src_list in league_map.items():
        if name in src_list:
            aliases.append(abbr)
    league_map[name] = aliases

# 3. 竞彩简称间的互相指向
for abbr in list(league_map.keys()):
    if abbr in ABBREV:
        others = [a for a in ABBREV[abbr] if a != abbr and a != abbr.replace('联赛','')]
        for o in others:
            if o not in league_map[abbr]:
                league_map[abbr].append(o)

with open(MAP_FILE, 'w', encoding='utf-8') as f:
    json.dump(league_map, f, ensure_ascii=False, indent=2)

print(f'生成 league_map.json: {len(league_map)} 个条目')

# 统计竞彩简称覆盖
abbr_count = sum(1 for k in league_map if k in ABBREV)
print(f'  竞彩简称覆盖: {abbr_count} 个')

# 测试
tests = ['英超','西甲','德甲','意甲','法甲','英冠','德乙','韩职','K1联赛','日职','J1','J2',
         '欧冠','欧联','欧协联','解放者杯','巴甲','阿甲','中超','澳超','美职联','荷甲','葡超']
print('\n=== 测试 ===')
for t in tests:
    if t in league_map:
        print(f'  [{len(league_map[t])}] {t}')
    else:
        print(f'  [X] {t}: 未找到')
