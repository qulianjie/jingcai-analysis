# -*- coding: utf-8 -*-
"""
最终报告生成器 V2 - 严格按RULES.md规则生成完整报告
包含所有24步的完整数据，不是摘要

用法:
    python final_report_generator.py <match目录路径> [输出路径]
"""
import os, sys, json, re
from _log_util import setup_logger
LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('final_report', LOG_DIR)


if len(sys.argv) < 2:
    log.info('Usage: python final_report_generator.py <match_dir_path> [output_path]')
    sys.exit(1)

MD = sys.argv[1]
OUTPUT_PATH = sys.argv[2] if len(sys.argv) > 2 else None

from _util import rd, re_find

def strip_heading(text):
    """去掉步骤文件自带的重复标题（如 '# 第1步：欧盘基础信息'）"""
    if not text:
        return text
    lines = text.split('\n')
    # Remove first line if it's a level-1 heading starting with '# 第'
    if lines and lines[0].startswith('# 第') and (':' in lines[0] or '\uff1a' in lines[0]):
        lines = lines[1:]
        # Also remove empty lines after heading
        while lines and not lines[0].strip():
            lines = lines[1:]
    return '\n'.join(lines)



# Paths
PARENT = os.path.dirname(MD)
G1 = os.path.join(MD, 'group01_europe')
G2 = os.path.join(MD, 'group02_handicap')
G3 = os.path.join(MD, 'group03_asian')
G4 = os.path.join(MD, 'group04_teamA')
G5 = os.path.join(MD, 'group05_teamB')
G6 = os.path.join(MD, 'group06_baijia')

# ============ Read ALL step files ============

# meta
meta_raw = rd(os.path.join(MD, 'meta.json'))
try:
    meta = json.loads(meta_raw) if meta_raw else {}
except:
    meta = {}

# Handle both meta formats
if 'match_info' in meta:
    mi = meta['match_info']
    match_no = mi.get('match_no', '001')
    MATCH_NAME = f"{mi.get('week','')}{match_no}_{mi.get('home_team','')}vs{mi.get('away_team','')}"
    FID = mi.get('fixtureid', '-')
    LEAGUE = mi.get('league', '-')
    MATCH_DATE = (mi.get('match_time','') or '').split('T')[0] if mi.get('match_time') else '-'
else:
    MATCH_NAME = meta.get('match', os.path.basename(MD))
    FID = meta.get('fid', '-')
    LEAGUE = meta.get('league', '-')
    MATCH_DATE = meta.get('date', '-')

# Group01: 欧赔基础 + 竞彩同赔 + Interwetten同赔 (Steps 1,2,3)
s1 = rd(os.path.join(G1, 'step1_europe_base.txt')) or rd(os.path.join(G1, 'step01_europe_basic.md'))
# Step 2: 竞彩同赔
s2 = rd(os.path.join(G1, 'step2_jingcai_same.txt')) or rd(os.path.join(G1, 'step02_jingcai_same.md'))
if not s2:
    s2 = rd(os.path.join(G2, 'step05_handicap_same.md'))
# Step 3: Interwetten同赔（独立读取step3文件）
s3 = rd(os.path.join(G1, 'step3_interwetten_same.txt')) or rd(os.path.join(G1, 'step03_interwetten_same.md'))
if not s3:
    s3 = rd(os.path.join(G2, 'step03_interwetten_same.md'))

# Group02: 让球基础 + 让球同赔 (Steps 4,5)
s4 = rd(os.path.join(G2, 'step4_handicap_base.txt')) or rd(os.path.join(G2, 'step04_handicap_basic.md'))
s5 = rd(os.path.join(G2, 'step5_handicap_same.txt')) or rd(os.path.join(G2, 'step05_handicap_same.md'))

# Group03: 亚盘基础 + 澳门同赔 + 联赛统计 (Steps 6,7,8)
s6 = rd(os.path.join(G3, 'step6_asian_base.txt')) or rd(os.path.join(G3, 'step06_asian_basic.md'))
s7 = rd(os.path.join(G3, 'step7_macau_same.txt')) or rd(os.path.join(G3, 'step07_macau_same.md'))
if not s7:
    s7 = rd(os.path.join(G3, 'step07_macau_same.json'))
s8_md = rd(os.path.join(G3, 'step8_same_league.txt'))
if not s8_md:
    for s8_name in ['step08_same_league.md', 'step08_league_asian.md']:
        s8_md = rd(os.path.join(G3, s8_name))
        if s8_md and '待完善' not in s8_md and '待补充' not in s8_md and s8_md.strip():
            break

# Group04: 主队主场分析 (Steps 9-13)
# step09_13_teamA.md already contains steps 9-13 all-in-one
s9_13 = rd(os.path.join(G4, 'step9_home_history.txt'))
if not s9_13:
    for s9_name in ['step09_13_teamA.md', 'step09_home_matches.md', 'step09_home_fixture.md']:
        s9_13 = rd(os.path.join(G4, s9_name))
        if s9_13:
            break

# Group05: 客队客场分析 (Steps 14-18)
# step14_18_teamB.md already contains steps 14-18 all-in-one
s14_18 = rd(os.path.join(G5, 'step14_away_history.txt'))
if not s14_18:
    for s14_name in ['step14_18_teamB.md', 'step14_away_matches.md', 'step14_away_fixture.md']:
        s14_18 = rd(os.path.join(G5, s14_name))
        if s14_18:
            break

# Group06: 百家对比分析 (Steps 19-23)
s19_23 = rd(os.path.join(G6, 'step19_baijia_compare.txt'))
if not s19_23:
    for s19_name in ['step19_baijia_extract.md', 'step19_23_baijia.md']:
        s19_23 = rd(os.path.join(G6, s19_name))
        if s19_23:
            break

# Step 24
s24 = ''
for s24_name in ['step24_panlu_match.json', 'step24_panlu_match.md']:
    s24 = rd(os.path.join(MD, s24_name))
    if s24:
        break

# Step 25
s25 = ''
for s25_name in ['step25_zhuangjia.json', 'step25_zhuangjia.md']:
    s25 = rd(os.path.join(MD, s25_name))
    if s25:
        break
if not s25:
    s25 = rd(os.path.join(PARENT, 'step25_zhuangjia.json'))

# Step 26 (from merged step25 data - written as step26_profit_ratio.json by step25_zhuangjia.py --all)
s26 = ''
for s26_name in ['step26_profit_ratio.json', 'step26_profit_ratio.md']:
    s26 = rd(os.path.join(MD, s26_name))
    if s26:
        break
if not s26:
    # Fallback: reconstruct from step25 raw data
    s26 = rd(os.path.join(MD, 'step25_zhuangjia.json'))
    if not s26:
        s26 = rd(os.path.join(PARENT, 'step25_zhuangjia.json'))
    if s26 and s26.strip().startswith('{'):
        try:
            s25_data_full = json.loads(s26)
            if 'data' in s25_data_full:
                from step25_zhuangjia import analyze_profit_ratio as _analyze_pr
                pa = _analyze_pr(s25_data_full['data'])
                analysis = pa['analysis']
                prd = pa['profit_ratio']
                analysis['盈亏占比'] = {k: v.get('ratio', 0) for k, v in prd.items()}
                analysis['投注占比'] = {k: v.get('bet_pct', '0') for k, v in prd.items()}
                s26 = json.dumps({'analysis': analysis, 'profit_ratio': prd})
            else:
                s26 = ''
        except:
            s26 = ''

# ============ Extract match info ============

# Team names - try multiple sources
home_team = ''
away_team = ''
# 1. From meta.json
home_team = meta.get('home', '')
away_team = meta.get('away', '')
# 2. From directory name (match001__神户胜利_大阪樱花)
if not home_team:
    dir_name = os.path.basename(MD)
    if '__' in dir_name:
        teams_part = dir_name.split('__', 1)[1]
        if '_' in teams_part:
            parts = teams_part.split('_')
            if len(parts) >= 2:
                home_team = parts[0]
                away_team = parts[1]
# 3. From MATCH_NAME
if not home_team and '_' in MATCH_NAME:
    teams = MATCH_NAME.split('_', 1)[1].replace('vs', 'VS')
    if 'VS' in teams:
        home_team = teams.split('VS')[0]
        away_team = teams.split('VS')[1]

# Match number - from meta.json first, then directory name
match_num = meta.get('matchnum', '')
if not match_num:
    dir_name = os.path.basename(MD)
    if '__' in dir_name:
        match_num = dir_name.split('__')[0].replace('match', '')
if not match_num:
    match_num = re_find(MATCH_NAME, r'^(周[一二三四五六日]\d+)')
if not match_num:
    match_num = MATCH_NAME.split('_')[0] if '_' in MATCH_NAME else '周一002'

hn = home_team or '主队'
an = away_team or '客队'

# Handicap
handicap_desc = re_find(s4, r'让球:\s*(.+)')
if not handicap_desc:
    s4_match = re.search(r'让球[数]?:\s*[-]?\d', s4)
    if s4_match:
        handicap_desc = s4_match.group(0).replace('让球数:', '').replace('让球:', '')
    else:
        handicap_desc = '主队-1球'

# Macau line - from meta.json (即时盘), strip 升/降 suffix
macau_line = meta.get('macau_line', '')
if macau_line:
    macau_line = macau_line.replace(' 升', '').replace(' 降', '').strip()
# Fallback: from s6 table row
if not macau_line:
    for line in s6.split('\n'):
        if '|' in line and '澳门' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                # 即时盘 is usually in the 3rd column
                pan_match = re.match(r'(.+?)\s+\d', parts[2])
                if pan_match:
                    macau_line = pan_match.group(1).strip()
                    break
if not macau_line:
    macau_line = re_find(s6, r'初盘:\s*(.+?)\s+\d') or '未知'

# ============ Generate Report ============

from datetime import datetime
now = datetime.now().strftime('%Y-%m-%d %H:%M')

# Run conclusion generator (direct import, no subprocess)
conclusion_md = '- 数据不足，无法生成结论'
try:
    from final_conclusion_generator import generate_conclusion
    text = generate_conclusion(MD)
    if text:
        conclusion_md = text
        log.info(f'[CONCLUSION] OK, length={len(conclusion_md)}')
    else:
        log.info(f'[CONCLUSION] empty result')
except Exception as e:
    log.info(f'[CONCLUSION] exception: {e}')

# Step 7 fallback
if not s7.strip():
    s7_content = '- 数据获取失败（AJAX接口不可用）'
else:
    s7_content = s7

# Step 8 check
if not s8_md.strip() or '待完善' in s8_md:
    s8_content = '- 数据待完善（step8未采集完成）'
else:
    s8_content = s8_md

# Step 24 - if json, format it
if s24.strip().startswith('{'):
    try:
        s24_data = json.loads(s24)
        s24_content = json.dumps(s24_data, ensure_ascii=False, indent=2)
    except:
        s24_content = s24
elif not s24.strip():
    s24_content = '- 数据获取失败'
else:
    s24_content = s24

# Step 25
s25 = ''
for s25_name in ['step25_zhuangjia.json', 'step25_zhuangjia.md']:
    s25 = rd(os.path.join(MD, s25_name))
    if s25:
        break
if not s25:
    s25 = rd(os.path.join(PARENT, 'step25_zhuangjia.json'))

s25_content = ''
if s25 and s25.strip().startswith('{'):
    try:
        s25_data = json.loads(s25)
        s25_labels = s25_data.get('labels', {})
        if s25_labels:
            s25_content = '| 项目 | 主胜 | 平局 | 客胜 |\n|------|------|------|------|\n'
            for cat in ['bet_pct', 'volume', 'profit']:
                cat_name = {'bet_pct': '投注占比', 'volume': '成交量', 'profit': '庄家盈亏'}.get(cat, cat)
                vals = [s25_labels.get(l, {}).get(cat, '-') for l in ['主胜', '平局', '客胜']]
                s25_content += '| {} | {} | {} | {} |\n'.format(cat_name, vals[0], vals[1], vals[2])
    except:
        s25_content = '- 解析失败'

# Step 26: 盈亏占比分析
s26_content = ''
if s26 and s26.strip().startswith('{'):
    try:
        s26_data = json.loads(s26)
        analysis = s26_data.get('analysis', {})
        profit_ratio = analysis.get('盈亏占比', {})
        bet_pct = analysis.get('投注占比', {})
        s26_content = '| 方向 | 盈亏占比 | 投注占比 | 庄家盈亏 |\n|------|------|------|------|\n'
        zhuang_map = {'胜': analysis.get('庄家胜盈亏', '-'), '平': analysis.get('庄家平盈亏', '-'), '负': analysis.get('庄家负盈亏', '-')}
        for label in ['胜', '平', '负']:
            ratio = str(profit_ratio.get(label, '-'))
            pct_raw = str(bet_pct.get(label, '-'))
            pct = pct_raw if pct_raw.endswith('%') else (pct_raw + '%')
            s26_content += '| {} | {} | {} | {} |\n'.format(label, ratio, pct, zhuang_map[label])
        s26_content += '\n### 综合分析\n'
        if analysis.get('庄家最看好'):
            s26_content += '- **庄家最看好**: {}\n'.format(analysis['庄家最看好'])
        s26_content += '- **庄家盈亏方向**: 胜:{} / 平:{} / 负:{}\n'.format(
            analysis.get('庄家胜盈亏', '-'),
            analysis.get('庄家平盈亏', '-'),
            analysis.get('庄家负盈亏', '-'))
    except Exception as e:
        s26_content = f'- 解析失败: {e}'

r = f"""# {match_num}_{hn}vs{an}

📅 报告时间: {now}
🔗 比赛: {LEAGUE} · {hn}vs{an}
🔗 比赛时间: {MATCH_DATE}
🔗 竞彩编号: {match_num}
🔗 让球: {handicap_desc}
🔗 澳门亚盘: {macau_line}
🔗 数据来源: odds.500.com + liansai.500.com

---

# 第一部分: 欧赔基础(步骤1-3)

## 第1步: 欧盘基础信息

{strip_heading(s1) if s1 else '- 数据获取失败'}

---

## 第2步: 欧盘・竞彩官网 相同赔率

{strip_heading(s2) if s2 else '- 数据获取失败'}

---

## 第3步: 欧盘・Interwetten 相同赔率

{strip_heading(s3) if s3 else '- 数据获取失败'}

---

# 第二部分: 让球指数(步骤4-5)

## 第4步: 让球指数基础信息

{strip_heading(s4) if s4 else '- 数据获取失败'}

---

## 第5步: 让球指数・竞彩官网 相同赔率

{strip_heading(s5) if s5 else '- 数据获取失败'}

---

# 第三部分: 亚盘对比(步骤6-8)

## 第6步: 亚盘对比基础信息

{strip_heading(s6) if s6 else '- 数据获取失败'}

---

## 第7步: 亚盘・澳门 相同盘口

{strip_heading(s7_content)}

---

## 第8步: 相同联赛相同亚盘统计

{strip_heading(s8_content)}

---

# 第四部分: 主队主场分析(步骤9-13)

## 主队主场・相同联赛・澳门亚盘同赔 + 欧赔/让球分析

{strip_heading(s9_13) if s9_13 else '- 数据获取失败'}

---

# 第五部分: 客队客场分析(步骤14-18)

## 客队客场・相同联赛・澳门亚盘同赔 + 欧赔/让球分析

{strip_heading(s14_18) if s14_18 else '- 数据获取失败'}

---

# 第六部分: 百家对比分析(步骤19-23)

{strip_heading(s19_23) if s19_23 else '- 数据获取失败'}

---

# 第七部分: 盘路完全匹配汇总(步骤24)

{strip_heading(s24_content)}

---

# 第八部分: 庄家盈亏分析(步骤25)

{s25_content if s25_content else '- 数据获取失败'}

---

# 第八部分续: 庄家盈亏占比分析(步骤26)

{s26_content if s26_content else '- 数据获取失败'}

---

# 第九部分: 最终结论(综合预测+投注建议)

{conclusion_md}

---

📋 生成时间: {now}
🤖 脚本: final_report_generator.py V2
📊 数据: sporttery.cn / odds.500.com / liansai.500.com
"""

# ============ Output ============

if not OUTPUT_PATH:
    # RULES.md: jingcai/tasks/{日期}/周几00几_主队vs客队.md
    # PARENT is data/ dir, need to go up one level to task dir
    TASK_DIR = os.path.dirname(PARENT)
    if '_' in MATCH_NAME:
        teams = MATCH_NAME.split('_', 1)[1]
    else:
        teams = MATCH_NAME
    # MATCH_NAME可能已经包含match_num前缀（如"周日001 蔚山现代vs富川FC"），需要去重
    teams_clean = teams.replace(' vs ', 'vs').replace('VS', 'vs')
    # 去除teams_clean中重复的match_num前缀
    teams_clean = re.sub(r'^' + re.escape(match_num) + r'[\s_]*', '', teams_clean)
    output_name = '{}_{}.md'.format(match_num, teams_clean)
    OUTPUT_PATH = os.path.join(TASK_DIR, output_name)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(r)

log.info(f'OK: {OUTPUT_PATH}')
log.info(f'Size: {os.path.getsize(OUTPUT_PATH)} bytes')
