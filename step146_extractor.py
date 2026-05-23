# -*- coding: utf-8 -*-
"""Step 1/4/6 合并提取器 - 欧赔/让球/亚盘基础数据（一次调用生成3个文件）
用法1: python step146_extractor.py <fid> <league> <output_step1> <output_step4> <output_step6>
用法2: python step146_extractor.py <match_dir>  (自动从 meta.json 读取 fid/league/home/away)
"""
import sys, os, requests, re, time, json
from bs4 import BeautifulSoup
from datetime import datetime

# 支持两种调用方式：match_dir 模式 或 参数模式
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    MATCH_DIR = sys.argv[1]
    meta_path = os.path.join(MATCH_DIR, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        FID = meta.get('fid', '1199680')
        LEAGUE = meta.get('league', '意甲')
        HOME = meta.get('home', '')
        AWAY = meta.get('away', '')
    else:
        FID = '1199680'
        LEAGUE = '意甲'
        HOME = AWAY = ''
    OUT1 = os.path.join(MATCH_DIR, 'group01_europe', 'step1_europe_base.txt')
    OUT4 = os.path.join(MATCH_DIR, 'group02_handicap', 'step4_handicap_base.txt')
    OUT6 = os.path.join(MATCH_DIR, 'group03_asian', 'step6_asian_base.txt')
else:
    FID = sys.argv[1] if len(sys.argv) > 1 else '1199680'
    LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '意甲'
    HOME = sys.argv[3] if len(sys.argv) > 3 else ''
    AWAY = sys.argv[4] if len(sys.argv) > 4 else ''
    OUT1 = sys.argv[5] if len(sys.argv) > 5 else ''
    OUT4 = sys.argv[6] if len(sys.argv) > 6 else ''
    OUT6 = sys.argv[7] if len(sys.argv) > 7 else ''

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

now = datetime.now().strftime('%Y-%m-%d %H:%M')

def dir_str(init_vals, live_vals):
    result = ''
    for a, b in zip(init_vals, live_vals):
        if b > a + 0.01: result += '⬆'
        elif b < a - 0.01: result += '⬇'
        else: result += '➡'
    return result

# ============================================================
# STEP 1: 欧赔基础
# ============================================================
html_ouzhi = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(FID), timeout=15)
html_ouzhi.encoding = 'gbk'
soup_ouzhi = BeautifulSoup(html_ouzhi.text, 'html.parser')

all_companies = []
for table in soup_ouzhi.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        td1 = tds[1].get_text().strip()
        nums = []
        for idx in [3, 4, 5, 6, 7, 8]:
            val = tds[idx].get_text().strip().replace(chr(160), '')
            try: nums.append(float(val))
            except: print(f'[欧赔] 数值转换失败: {val}', file=sys.stderr)
        if len(nums) >= 6:
            if td0.isdigit():
                all_companies.append({'row_num': int(td0), 'name': td1,
                    'iw': nums[0], 'id': nums[1], 'il': nums[2],
                    'lw': nums[3], 'ld': nums[4], 'll': nums[5], 'is_avg': False})
            elif '平均值' in td1:
                all_companies.append({'row_num': 99, 'name': '百家平均',
                    'iw': nums[0], 'id': nums[1], 'il': nums[2],
                    'lw': nums[3], 'ld': nums[4], 'll': nums[5], 'is_avg': True})

jc_data = iw_data = av_data = None
for c in all_companies:
    if c['row_num'] == 1: jc_data = c
    elif c['row_num'] == 6: iw_data = c
    elif c['is_avg']: av_data = c

lines1 = []
lines1.append('=' * 70)
lines1.append('竞彩足球 · 欧赔基础信息')
lines1.append('=' * 70)
lines1.append('')
lines1.append('📅 数据获取时间: ' + now)
lines1.append('📊 比赛: {} · FID: {}'.format(LEAGUE, FID))
lines1.append('')
lines1.append('| 公司 | 初盘胜 | 初盘平 | 初盘负 | 即时胜 | 即时平 | 即时负 | 变化 |')
lines1.append('|------|-------|-------|-------|-------|-------|-------|------|')

if jc_data:
    jcd = dir_str((jc_data['iw'], jc_data['id'], jc_data['il']), (jc_data['lw'], jc_data['ld'], jc_data['ll']))
    lines1.append('| 竞彩官方 | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {} |'.format(
        jc_data['iw'], jc_data['id'], jc_data['il'], jc_data['lw'], jc_data['ld'], jc_data['ll'], jcd))
if iw_data:
    iwd = dir_str((iw_data['iw'], iw_data['id'], iw_data['il']), (iw_data['lw'], iw_data['ld'], iw_data['ll']))
    lines1.append('| Interwetten | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {} |'.format(
        iw_data['iw'], iw_data['id'], iw_data['il'], iw_data['lw'], iw_data['ld'], iw_data['ll'], iwd))
if av_data:
    avd = dir_str((av_data['iw'], av_data['id'], av_data['il']), (av_data['lw'], av_data['ld'], av_data['ll']))
    lines1.append('| 百家平均 | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {} |'.format(
        av_data['iw'], av_data['id'], av_data['il'], av_data['lw'], av_data['ld'], av_data['ll'], avd))

lines1.append('')
lines1.append('---')
lines1.append('')
lines1.append('提取完成！')
lines1.append('  竞彩/Interwetten/百家平均 (3家)')

# ============================================================
# 提取球队ID + 澳门亚盘（写入meta.json）
# 关键修复：先获取yazhi页面，再提取
# ============================================================
HOME_ID = ''
AWAY_ID = ''
MACAU_LINE = ''

try:
    # 先获取亚盘页面（这是提取球队ID和澳门亚盘的前提）
    html_yz_extract = sess.get('https://odds.500.com/fenxi/yazhi-{}.shtml'.format(FID), timeout=15)
    html_yz_extract.encoding = 'gbk'
    soup_yz_extract = BeautifulSoup(html_yz_extract.text, 'html.parser')

    # === 方法1: 从 yazhi 页面提取球队ID ===
    for table in soup_yz_extract.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 2: continue
            name_col = tds[1].get_text().strip() if len(tds) > 1 else ''
            if HOME and HOME in name_col:
                for a in (tds[1].find_all('a', href=True) if len(tds) > 1 else []):
                    tm = re.search(r'/team/(\d+)/', a.get('href', ''))
                    if tm:
                        HOME_ID = tm.group(1)
                        break
            if AWAY and AWAY in name_col:
                for a in (tds[1].find_all('a', href=True) if len(tds) > 1 else []):
                    tm = re.search(r'/team/(\d+)/', a.get('href', ''))
                    if tm:
                        AWAY_ID = tm.group(1)
                        break

    # === 方法2: 从 ouzhi 页面提取球队ID（回退） ===
    if not HOME_ID or not AWAY_ID:
        team_links = []
        for a in soup_ouzhi.find_all('a', href=True):
            href = a.get('href', '')
            tm = re.search(r'/team/(\d+)/', href)
            if tm:
                atxt = a.get_text().strip()
                if atxt:
                    team_links.append((tm.group(1), atxt))
        seen = set()
        for tid, txt in team_links:
            if tid not in seen:
                seen.add(tid)
                if not HOME_ID:
                    HOME_ID = tid
                elif HOME_ID != tid and not AWAY_ID:
                    AWAY_ID = tid
                    break

    # === 提取澳门亚盘 ===
    for table in soup_yz_extract.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12: continue
            name = tds[1].get_text().strip()
            if '澳门' in name:
                for idx in [3, 4, 5, 10, 11]:
                    if idx < len(tds):
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        if any(c in val for c in ['让', '球', '半', '盘', '受让']):
                            # 去掉方向箭头、换行、数字、水位
                            val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                            val = re.sub(r'[\d\.]+', '', val).strip()
                            # 去掉升降水标记
                            val = val.replace('升', '').replace('降', '').strip()
                            if val:
                                MACAU_LINE = val
                                break
                if MACAU_LINE: break
        if MACAU_LINE: break

    # 回退：从第一行提取盘口
    if not MACAU_LINE:
        for table in soup_yz_extract.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0 in ['1', '2', '3']:
                    for idx in range(len(tds)):
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        if any(c in val for c in ['让', '球', '半', '受让']) and not val.isdigit():
                            val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                            val = re.sub(r'[\d\.]+', '', val).strip()
                            val = val.replace('升', '').replace('降', '').strip()
                            if val:
                                MACAU_LINE = val
                                break
                    if MACAU_LINE: break
            if MACAU_LINE: break

    # === 写入meta.json ===
    if HOME_ID or AWAY_ID or MACAU_LINE:
        meta_file = os.path.join(MATCH_DIR, 'meta.json') if os.path.isdir(MATCH_DIR) else None
        if meta_file and os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as mf:
                meta_up = json.load(mf)
            if HOME_ID: meta_up['home_id'] = HOME_ID
            if AWAY_ID: meta_up['away_id'] = AWAY_ID
            if MACAU_LINE: meta_up['macau_line'] = MACAU_LINE
            with open(meta_file, 'w', encoding='utf-8') as mf:
                json.dump(meta_up, mf, ensure_ascii=False, indent=2)
            print('Team IDs: home=%s, away=%s, macau_line=%s' % (HOME_ID, AWAY_ID, MACAU_LINE))
        else:
            print('meta.json 不存在')
    else:
        print('球队ID和澳门亚盘全部提取失败！')

except Exception as e:
    print('提取球队ID/澳门亚盘失败: %s' % e)

# ============================================================
# STEP 4: 让球基础
# ============================================================
html_rq = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(FID), timeout=15)
html_rq.encoding = 'gbk'
soup_rq = BeautifulSoup(html_rq.text, 'html.parser')

rq_jc = None
for table in soup_rq.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        td2 = tds[2].get_text().strip().replace(chr(160), '')
        if td0 == '1':
            nums = []
            for idx in [4, 5, 6, 7, 8, 9]:
                val = tds[idx].get_text().strip().replace(chr(160), '')
                try: nums.append(float(val))
                except: print(f'[亚盘] 数值转换失败: {val}', file=sys.stderr)
            if len(nums) >= 6:
                rq_jc = {'handicap': td2, 'iw': nums[0], 'id': nums[1], 'il': nums[2],
                    'lw': nums[3], 'ld': nums[4], 'll': nums[5]}

lines4 = []
lines4.append('=' * 70)
lines4.append('竞彩足球 · 让球基础信息')
lines4.append('=' * 70)
lines4.append('')
lines4.append('📅 数据获取时间: ' + now)
lines4.append('📊 比赛: {} · FID: {}'.format(LEAGUE, FID))
lines4.append('')
lines4.append('| 公司 | 让球 | 初盘胜 | 初盘平 | 初盘负 | 即时胜 | 即时平 | 即时负 |')
lines4.append('|------|------|-------|-------|-------|-------|-------|-------|')

if rq_jc:
    lines4.append('| 竞彩官方 | {} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |'.format(
        rq_jc['handicap'], rq_jc['iw'], rq_jc['id'], rq_jc['il'], rq_jc['lw'], rq_jc['ld'], rq_jc['ll']))

lines4.append('')
lines4.append('---')
lines4.append('')
lines4.append('提取完成！')
lines4.append('  竞彩官方 (1家)')

# ============================================================
# STEP 6: 亚盘基础
# ============================================================
# 复用之前获取的 soup_yz_extract，不再重复请求
soup_yz = soup_yz_extract

target_rows_yz = [1, 2, 3]
yz_data = []
for table in soup_yz.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 10: continue
        td0 = tds[0].get_text().strip()
        if td0.isdigit() and int(td0) in target_rows_yz:
            name = tds[1].get_text().strip()
            iiw = iil = liw = lil = ''
            ll_text = ''  # 初盘盘口 (ll = live line? 实为变量名约定, 表格格式用ll_text/liw/lil当初盘组)
            il_text = ''  # 即时盘盘口 (il = "immediate line"? 表格格式用il_text/iiw/iil当即时盘组)
            for idx in range(len(tds)):
                val = tds[idx].get_text().strip().replace(chr(160), '')
                if idx == 4:
                    # td[4] = 初盘盘口文字
                    ll_text = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194⬆⬇➡]', '', val).strip()
                elif idx == 3:
                    m = re.search(r'([\d\.]+)', val)
                    if m: liw = m.group(1)  # 初盘主水（配合表格格式，liw用在初盘组）
                elif idx == 5:
                    m = re.search(r'([\d\.]+)', val)
                    if m: lil = m.group(1)  # 初盘客水
                elif idx == 10:
                    # td[10] = 即时盘盘口文字
                    il_text = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194⬆⬇➡]', '', val).strip()
                elif idx == 9:
                    m = re.search(r'([\d\.]+)', val)
                    if m: iiw = m.group(1)  # 即时盘主水（配合表格格式，iiw用在即时盘组）
                elif idx == 11:
                    m = re.search(r'([\d\.]+)', val)
                    if m: iil = m.group(1)  # 即时盘客水
            yz_data.append({'row_num': int(td0), 'name': name,
                'il_text': il_text, 'liw': liw, 'lil': lil,
                'iiw': iiw, 'iil': iil, 'll_text': ll_text})

company_map = {1: '威廉希尔', 2: '澳门', 3: '立博'}

lines6 = []
lines6.append('=' * 70)
lines6.append('竞彩足球 · 亚盘基础信息')
lines6.append('=' * 70)
lines6.append('')
lines6.append('📅 数据获取时间: ' + now)
lines6.append('📊 比赛: {} · FID: {}'.format(LEAGUE, FID))
lines6.append('')
lines6.append('| 公司 | 初盘 | 即时盘 |')
lines6.append('|------|------|--------|')

for d in yz_data:
    cn = company_map.get(d['row_num'], d['name'])
    lines6.append('| {} | {}（主水{}|客水{}） | {}（主水{}|客水{}） |'.format(
        cn, d['ll_text'], d['liw'], d['lil'], d['il_text'], d['iiw'], d['iil']))

lines6.append('')
lines6.append('---')
lines6.append('')
lines6.append('提取完成！')
lines6.append('  威廉希尔/澳门/立博 (3家)')

# ============================================================
# 写入文件
# ============================================================
if OUT1:
    os.makedirs(os.path.dirname(os.path.abspath(OUT1)), exist_ok=True)
    with open(OUT1, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines1))
    print('Step 1: %s' % OUT1.split(os.sep)[-1] if os.sep in OUT1 else OUT1)

if OUT4:
    os.makedirs(os.path.dirname(os.path.abspath(OUT4)), exist_ok=True)
    with open(OUT4, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines4))
    print('Step 4: %s' % OUT4.split(os.sep)[-1] if os.sep in OUT4 else OUT4)

if OUT6:
    os.makedirs(os.path.dirname(os.path.abspath(OUT6)), exist_ok=True)
    with open(OUT6, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines6))
    print('Step 6: %s' % OUT6.split(os.sep)[-1] if os.sep in OUT6 else OUT6)
