# -*- coding: utf-8 -*-
"""05-09 竞彩预测=平 AND 庄家看好=平 的比赛"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

date = '2026-05-09'
date_dir = os.path.join(TASKS_DIR, date)
data_dir = os.path.join(date_dir, 'data')

# Build report map
report_map = {}
for f in glob.glob(os.path.join(date_dir, '周*.md')):
    m = re.match(r'(周[一二三四五六日]\d+)[_]', os.path.basename(f))
    if m:
        mn = m.group(1)
        content = rd(f)
        pred_m = re.search(r'\*\*竞彩预测\*\*\s*\|\s*([^（|]+)', content)
        conf_m = re.search(r'\*\*信心\*\*\s*\|\s*(\d+)%', content)
        league_m = re.search(r'🔗 比赛: ([^·]+)', content)
        asian_m = re.search(r'澳门亚盘:\s*(.+)', content)
        handicap_m = re.search(r'让球:\s*(.+)', content)
        report_map[mn] = {
            'content': content,
            'pred': pred_m.group(1).strip() if pred_m else '',
            'conf': conf_m.group(1) + '%' if conf_m else '',
            'league': league_m.group(1).strip() if league_m else '',
            'asian': asian_m.group(1).strip() if asian_m else '',
            'handicap': handicap_m.group(1).strip() if handicap_m else '',
        }

# Build step26 map from match dirs
step26_map = {}
if os.path.exists(data_dir):
    for md in os.listdir(data_dir):
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        meta = json.loads(rd(os.path.join(md_path, 'meta.json'))) if os.path.exists(os.path.join(md_path, 'meta.json')) else {}
        mn = meta.get('matchnum', '')
        s26_path = os.path.join(md_path, 'step26_profit_ratio.json')
        if os.path.exists(s26_path) and mn:
            s26 = json.loads(rd(s26_path))
            step26_map[mn] = s26.get('analysis', {})

# Find matches where BOTH 竞彩预测=平 AND 庄家看好=平
print('=' * 70)
print('05-09 竞彩预测=平 AND 庄家看好=平')
print('=' * 70)

both_draw = []
for mn, info in sorted(report_map.items()):
    if info['pred'] not in ['平', '平局']:
        continue
    
    s26 = step26_map.get(mn, {})
    zhuangjia_best = s26.get('庄家最看好', '')
    
    if zhuangjia_best not in ['平局', '平']:
        print(f'\n⚠️  {mn} {info["league"]}: 预测=平, 但庄家看好={zhuangjia_best} → 不一致')
        continue
    
    bet_ratio = s26.get('投注占比', {})
    profit_ratio = s26.get('盈亏占比', {})
    
    both_draw.append(mn)
    
    print(f'\n{"="*60}')
    print(f'📌 {mn} {info["league"]}')
    print(f'   竞彩预测: {info["pred"]} | 信心: {info["conf"]}')
    print(f'   让球: {info["handicap"]}')
    print(f'   澳门亚盘: {info["asian"]}')
    print(f'   庄家最看好: {zhuangjia_best}')
    print(f'   庄家盈亏: 胜={s26.get("庄家胜盈亏","?")}, 平={s26.get("庄家平盈亏","?")}, 负={s26.get("庄家负盈亏","?")}')
    print(f'   投注占比: 胜={bet_ratio.get("胜","?")}%, 平={bet_ratio.get("平","?")}%, 负={bet_ratio.get("负","?")}%')
    print(f'   盈亏占比: 胜={profit_ratio.get("胜","?")}, 平={profit_ratio.get("平","?")}, 负={profit_ratio.get("负","?")}')

print(f'\n{"="*70}')
print(f'📊 统计')
print(f'{"="*70}')
print(f'竞彩预测=平: {sum(1 for v in report_map.values() if v["pred"] in ["平","平局"])} 场')
print(f'庄家看好=平: {len(step26_map)} 场 (step26数据)')
print(f'两者同时=平: {len(both_draw)} 场')
print(f'两者同时=平的编号: {", ".join(both_draw)}')
