# -*- coding: utf-8 -*-
"""
更新 step8_1923_extractor.py 中的 LEAGUE_ID_MAP
用正确的联赛ID替换旧的ID
"""
import json

# 正确的联赛ID（从球队赛程页面提取）
CORRECT_LEAGUE_IDS = {
    '西甲': '9124',
    '英超': '9110',
    '意甲': '9116',
    '德甲': '9119',
    '法甲': '9122',
    '荷甲': '9125',
    '葡超': '9128',
    '韩职': '9131',
    '挪超': '9134',
    '瑞超': '9137',
    '丹超': '9140',
    '比甲': '9143',
    '土超': '9146',
    '俄超': '9149',
    '巴甲': '9152',
    '阿甲': '9155',
    '美职足': '9158',
    '沙特': '9161',
    '芬超': '9164',
    '荷乙': '9167',
    '德乙': '9170',
    '法乙': '9173',
    '意乙': '9176',
    '西乙': '9179',
    '解放者杯': '9182',
    '欧冠': '9185',
    '欧联': '9188',
}

# 读取 step8_1923_extractor.py
script_path = 'jingcai/step8_1923_extractor.py'
with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 更新 LEAGUE_ID_MAP
# 找到 LEAGUE_ID_MAP = { ... } 的部分
import re

# 替换联赛ID
for league, new_id in CORRECT_LEAGUE_IDS.items():
    # 匹配 '西甲': '19496' 格式
    pattern = r"('%s':\s*)'\d+'" % league.replace('(', '\(').replace(')', '\)')
    replacement = r"\1'%s'" % new_id
    content = re.sub(pattern, replacement, content)

# 写回文件
with open(script_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated LEAGUE_ID_MAP with correct league IDs')
print('Changed %d league IDs' % len(CORRECT_LEAGUE_IDS))
