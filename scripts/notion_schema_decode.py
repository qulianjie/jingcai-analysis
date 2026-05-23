#!/usr/bin/env python3
# Decode hex property names and map to Chinese
hex_names = {
    'e4b8bbe9989fe4b8bbe59cba': '主队主场',
    'e58f8de9a688e680bbe7bb93': '反馈总结',
    'e58f8de9a688e697a5e69c9f': '反馈日期',
    'e5a487e6b3a8': '备注',
    'e5ae9ee99985e6af94e58886': '实际比分',
    'e5ae9ee99985e7bb93e69e9c': '实际结果',
    'e5aea2e9989fe5aea2e59cba': '客队客场',
    'e6aca7e8b594e8b68be58abf': '欧赔趋势',
    'e6ada532355fe5ba84e5aeb6e79b88e4ba8f': '第25_庄家盈利',
    'e6ada532365fe5ba84e5aeb6e69c80e79c8be5a5bd': '第26_庄家最看好',
    'e6ada532365fe5ba84e5aeb6e79b88e4ba8fe696b9e59091': '第26_庄家盈利方向',
    'e6ada532365fe68a95e6b3a8e58da0e6af94': '第26_投注占比',
    'e6ada532365fe79b88e4ba8fe58da0e6af94': '第26_盈利占比',
    'e6af94e8b59b': '比赛',
    'e6af94e8b59be697a5e69c9f': '比赛日期',
    'e6beb3e997a8e4ba9ae79b98': '澳门亚盘',
    'e799bee5aeb6e5afb9e6af94': '百家对比',
    'e799bee5aeb6e6aca7e8b594e5b9b3': '百家欧赔平',
    'e799bee5aeb6e6aca7e8b594e8839c': '百家欧赔胜',
    'e799bee5aeb6e6aca7e8b594e8b49f': '百家欧赔负',
    'e7ab9ee5bda9e6aca7e8b594e5b9b3': '竞彩欧赔平',
    'e7ab9ee5bda9e6aca7e8b594e8839c': '竞彩欧赔胜',
    'e7ab9ee5bda9e6aca7e8b594e8b49f': '竞彩欧赔负',
    'e7ab9ee5bda9e6beb3e997a8e4ba9ae79b98': '竞彩澳门亚盘',
    'e7ab9ee5bda9e9a284e6b58b': '竞彩预测',
    'e7bb88e79b98496e74657277657474656ee5b9b3': '终盘Interwetten平',
    'e7bb88e79b98496e74657277657474656ee8839c': '终盘Interwetten胜',
    'e7bb88e79b98496e74657277657474656ee8b49f': '终盘Interwetten负',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e5b9b3': '终盘百家欧赔平',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e8839c': '终盘百家欧赔胜',
    'e7bb88e79b98e799bee5aeb6e6aca7e8b594e8b49f': '终盘百家欧赔负',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e5b9b3': '终盘竞彩欧赔平',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e8839c': '终盘竞彩欧赔胜',
    'e7bb88e79b98e7ab9ee5bda9e6aca7e8b594e8b49f': '终盘竞彩欧赔负',
    'e7bb88e79b98e7ab9ee5bda9e6beb3e997a8e4ba9ae79b98': '终盘竞彩澳门亚盘',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e5b9b3': '终盘让球指数平',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e8839c': '终盘让球指数胜',
    'e7bb88e79b98e8aea9e79083e68c87e695b0e8b49f': '终盘让球指数负',
    'e8aea9e79083e68c87e695b0e5b9b3': '让球指数平',
    'e8aea9e79083e68c87e695b0e8839c': '让球指数胜',
    'e8aea9e79083e68c87e695b0e8b49f': '让球指数负',
    'e8aea9e79083e9a284e6b58b': '让球预测',
    'e8aea9e79083e9a284e6b58be6ada3e7a1ae': '让球预测正确',
    'e9a284e6b58be6ada3e7a1ae': '预测正确',
    'e9a38ee999a9e68f90e7a4ba': '风险提示',
    '4957e5908ce8b594': 'IW同赔',
    '496e74657277657474656ee5b9b3': 'Interwetten平',
    '496e74657277657474656ee8839c': 'Interwetten胜',
    '496e74657277657474656ee8b49f': 'Interwetten负',
}

print('Notion竞彩数据库 - 属性名翻译对照表')
print('='*60)
hex_to_cn = {}
for h, cn in sorted(hex_names.items()):
    h2 = bytes.fromhex(h).decode('utf-8')
    hex_to_cn[h2] = cn
    print(f'  {cn}')

print(f'\n共{len(hex_names)}个属性')

# Core matching fields
print('\n\n用于历史匹配的核心字段:')
print('='*60)
match_fields = [
    ('竞彩欧赔胜', 'number', '本场初盘竞彩主胜赔率'),
    ('竞彩欧赔平', 'number', '本场初盘竞彩平赔率'),
    ('竞彩欧赔负', 'number', '本场初盘竞彩客胜赔率'),
    ('让球指数胜', 'number', '本场初盘让球胜赔率'),
    ('让球指数平', 'number', '本场初盘让球平赔率'),
    ('让球指数负', 'number', '本场初盘让球负赔率'),
    ('Interwetten胜', 'number', 'IWC初盘主胜'),
    ('Interwetten平', 'number', 'IWC初盘平'),
    ('Interwetten负', 'number', 'IWC初盘客负'),
    ('百家欧赔胜', 'number', '百家初盘主胜均值'),
    ('百家欧赔平', 'number', '百家初盘平均值'),
    ('百家欧赔负', 'number', '百家初盘客负均值'),
    ('竞彩澳门亚盘', 'rich_text', '澳门亚盘(初盘)'),
    ('实际比分', 'rich_text', '历史比赛实际比分'),
    ('实际结果', 'rich_text', '历史比赛实际赛果(胜/平/负)'),
]
for field, ftype, desc in match_fields:
    print(f'  {field:20s} [{ftype:10s}] {desc}')
