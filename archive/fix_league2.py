# -*- coding: utf-8 -*-
"""从最终报告.md文件中提取league信息，补回feedback.json"""
import json, os, re

FB = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# 已知联赛列表
KNOWN_LEAGUES = [
    '英超', '西甲', '德甲', '意甲', '法甲', '荷甲', '葡超', '俄超', '比甲',
    '瑞士超', '挪超', '瑞典超', '芬超', '丹超', '苏超', '澳超', '日职', 
    '日联', '韩职', '沙特职业联赛', '英冠', '土超', '阿甲', '巴甲', '中超',
    '美职联', '墨超', '解放者杯', '欧冠', '欧联', '欧协联', '世界杯',
    '欧洲杯', '美洲杯', '亚洲杯', '非洲杯', '友谊赛', '欧冠杯', '欧会杯',
    '球会友谊', '欧青联', '南美解放者杯', '南美杯', '世俱杯',
    '西班牙人', '德国杯', '法国杯', '英格兰足总杯', '英格兰联赛杯',
    '意杯', '荷兰杯', '比利时杯', '瑞士杯', '挪威杯', '瑞典杯',
    '芬兰杯', '丹麦杯', '苏格兰杯', '澳洲杯', '日联杯', '韩国杯',
    '沙特国王杯', '英超杯', '西超杯', '德超杯', '意超杯', '法超杯',
    '欧超杯', '欧洲国家联赛', '欧国联', '世界杯外围赛', '世预赛',
    '南美预选', '非洲预选', '亚洲杯外围赛', '亚洲杯外围', '欧预赛',
    '阿乙', '巴圣锦', '巴保罗', '巴帕尔尼', '巴米内', '巴东北',
    '阿超', '巴甲', '巴乙', '智甲', '哥甲', '秘甲', '委内甲', '厄甲', '乌拉甲', '巴拉甲', '哥伦甲',
    '波甲', '捷甲', '奥甲', '荷乙', '德乙', '法乙', '西乙', '英甲', '英乙',
    '苏冠', '苏甲', '苏乙', '瑞甲', '芬甲', '丹甲', '丹乙', '挪甲', '冰甲',
    '瑞士甲', '奥乙', '比乙', '土超', '土甲', '俄甲', '哈萨超', '乌兹超',
    '印甲', '泰超', '越南甲', '马来超', '新加坡', '印尼超', '以甲', '波兰超',
    '波兰甲', '罗甲', '克甲', '塞尔超', '斯洛伐', '斯洛文', '匈牙利',
    '阿尔巴', '保加', '塞浦路', '摩尔多', '北马其', '冰联杯', '阿联酋',
    '卡塔尔', '伊朗超', '伊拉克', '巴林超', '阿曼超', '科威超',
    '约旦超', '巴勒斯坦', '黎巴超', '阿富汗', '土库曼', '塔吉超',
    '吉尔吉斯', '尼泊尔', '孟加拉', '斯里兰', '马尔代夫', '柬埔寨',
    '老挝', '缅甸', '汶莱', '东帝汶', '菲律宾', '蒙古', '中国',
    '日本', '韩国', '朝鲜', '印度', '巴基斯坦', '锡金',
    '不丹', '马尔代夫', '斯里兰卡', '孟加拉', '尼泊尔', '柬埔寨',
    '老挝', '缅甸', '泰国', '越南', '菲律宾', '印尼', '马来', '新加坡',
    '文莱', '东帝汶', '关岛', '北马里亚纳', '帕劳', '密克罗', '马绍尔',
    '瑙鲁', '图瓦卢', '基里巴斯', '萨摩亚', '汤加', '斐济', '瓦努阿图',
    '所罗门', '库克群岛', '塔希提', '纽卡', '法波利', '新喀里',
    '新西兰', '澳洲', '美国', '加拿大', '墨西哥', '古巴', '海地',
    '多米尼加', '牙买加', '特立尼达', '巴哈马', '百慕大', '波多黎各',
    '哥斯达', '巴拿马', '洪都拉斯', '尼加拉瓜', '危地马拉', '萨尔瓦多',
    '伯利兹', '厄瓜多', '哥伦比亚', '委内瑞拉', '圭亚那', '苏里南',
    '法属圭', '巴西', '阿根廷', '智利', '秘鲁', '玻利维亚', '巴拉圭',
    '乌拉圭', '葡萄牙', '西班牙', '法国', '德国', '意大利', '荷兰',
    '比利时', '瑞士', '奥地利', '丹麦', '瑞典', '挪威', '芬兰',
    '冰岛', '英格兰', '苏格兰', '威尔士', '北爱尔兰', '爱尔兰',
    '波兰', '捷克', '斯洛伐', '匈牙利', '罗马尼亚', '保加利亚',
    '塞尔维亚', '克罗地亚', '斯洛文', '波黑', '黑山', '马其顿',
    '阿尔巴尼亚', '希腊', '土耳其', '塞浦路斯', '马耳他',
    '卢森堡', '列支敦', '摩纳哥', '安道尔', '圣马力', '直布罗',
    '科索沃', '拉脱维亚', '立陶宛', '爱沙尼亚', '白俄罗斯',
    '摩尔多瓦', '乌克兰', '俄罗斯', '格鲁吉亚', '亚美尼亚',
    '阿塞拜疆', '哈萨克斯坦', '乌兹别克', '土库曼', '塔吉克斯坦',
    '吉尔吉斯', '巴基斯坦', '印度', '斯里兰卡', '孟加拉', '尼泊尔',
    '不丹', '马尔代夫', '阿富汗', '伊朗', '伊拉克', '叙利亚',
    '黎巴嫩', '约旦', '巴勒斯坦', '以色列', '沙特', '科威特',
    '巴林', '卡塔尔', '阿联酋', '阿曼', '也门', '埃及', '利比亚',
    '突尼斯', '阿尔及利亚', '摩洛哥', '苏丹', '南苏丹', '埃塞俄',
    '厄立特里', '吉布提', '索马里', '肯尼亚', '乌干达', '坦桑尼亚',
    '卢旺达', '布隆迪', '刚果(布)', '刚果(金)', '安哥拉', '赞比亚',
    '津巴布韦', '博茨瓦纳', '纳米比亚', '南非', '斯威士兰', '莱索托',
    '马拉维', '莫桑比', '马达加斯', '毛里求斯', '塞舌尔', '科摩罗',
    '佛得角', '几内亚比', '塞内加尔', '冈比亚', '几内亚', '塞拉利',
    '利比里亚', '科特迪', '加纳', '多哥', '贝宁', '尼日尔',
    '布基纳法', '马里', '毛里塔', '西撒哈拉', '乍得', '中非',
    '喀麦隆', '赤道几', '加蓬', '中非共和国', '中非',
]

# Build league regex pattern - match any known league name
league_pattern = '|'.join(re.escape(l) for l in KNOWN_LEAGUES)

# Step 1: Scan all .md files for league info
md_league_map = {}
for date_dir in sorted(os.listdir(TASKS_DIR)):
    if not re.match(r'\d{4}-\d{2}-\d{2}', date_dir):
        continue
    task_path = os.path.join(TASKS_DIR, date_dir)
    if not os.path.isdir(task_path):
        continue
    
    for fname in os.listdir(task_path):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(task_path, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Find match number from filename
            mn_match = re.search(r'(周[一二三四五六日])(\d+)', fname)
            if not mn_match:
                continue
            weekday = mn_match.group(1)
            num = mn_match.group(2).zfill(3)
            match_num = weekday + num
            
            # Find league in the report header
            # Common formats:
            # "联赛: XXX"
            # "🔗 比赛: XXX · 主队vs客队"
            header = content[:2000]
            
            league = None
            # Try "联赛: XXX"
            m = re.search(r'联赛[:\s]+([^\n·]+)', header)
            if m:
                league = m.group(1).strip()
            
            if not league:
                # Try from match info line like "比赛: 英超 · 主队vs客队"
                m = re.search(r'比赛[:\s]+([^\n·]+?)[·\s]+', header)
                if m:
                    potential = m.group(1).strip()
                    # Check if it matches a known league
                    for kl in KNOWN_LEAGUES:
                        if kl in potential or potential in kl:
                            league = kl
                            break
            
            if league:
                key = f'{date_dir}_{match_num}'
                md_league_map[key] = league
        except:
            continue

print('Built md_league_map: %d entries' % len(md_league_map))
print('Sample:')
for k, v in list(md_league_map.items())[:10]:
    print('  %s -> %s' % (k, v))

# Step 2: Fix feedback.json
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', {})
fixed = 0

for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        current_league = item.get('league', '')
        if current_league and current_league != '未知':
            continue  # already has valid league
        
        match_num = item.get('match_num', '')
        if not match_num:
            continue
        
        key = f'{date}_{match_num}'
        
        if key in md_league_map:
            item['league'] = md_league_map[key]
            fixed += 1
        else:
            # Try normalize match_num
            m = re.match(r'(周[一二三四五六日])(\d+)$', match_num)
            if m:
                normalized = m.group(1) + m.group(2).zfill(3)
                key2 = f'{date}_{normalized}'
                if key2 in md_league_map:
                    item['league'] = md_league_map[key2]
                    fixed += 1
                    continue
            
            # Still not found - try to keep "未知"
            if not current_league:
                item['league'] = '未知'

# Save
with open(FB, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Fixed from reports: %d' % fixed)

# Step 3: Verify
with open(FB, 'r', encoding='utf-8') as f:
    data = json.load(f)
dates = data.get('dates', {})
league_counts = {}
total = 0
for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        total += 1
        league = item.get('league', '未知')
        league_counts[league] = league_counts.get(league, 0) + 1

print()
print('Total: %d' % total)
print('Unknown: %d' % league_counts.get('未知', 0))
print('League distribution (top 20):')
for league, count in sorted(league_counts.items(), key=lambda x: -x[1])[:20]:
    print('  %s: %d' % (league, count))
