# -*- coding: utf-8 -*-
"""
补全 feedback.json 特征 - 用(date, match_num)做唯一键
"""
import os, sys, json, re, glob

try:
    from _util import ensure_utf8_stdout
    ensure_utf8_stdout()
except: pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')


def build_dir_map():
    """(date, match_num) → dir_path"""
    dmap = {}
    if not os.path.exists(TASKS_DIR): return dmap
    for date in sorted(os.listdir(TASKS_DIR)):
        dd = os.path.join(TASKS_DIR, date)
        if not os.path.isdir(dd) or not date.startswith('2026-'): continue
        data_dir = os.path.join(dd, 'data')
        base = data_dir if os.path.isdir(data_dir) else dd
        for sub in os.listdir(base):
            sp = os.path.join(base, sub)
            if not os.path.isdir(sp) or not sub.startswith('match'): continue
            meta_file = os.path.join(sp, 'meta.json')
            if not os.path.exists(meta_file): continue
            try:
                meta = json.loads(open(meta_file, 'r', encoding='utf-8').read())
                mn = meta.get('matchnum', '')
                mn_clean = re.sub(r'^周[一二三四五六日]', '', mn)
                key = (date, mn_clean)
                dmap[key] = {
                    'dir': sp,
                    'meta': meta,
                    'date': date,
                    'mn': mn_clean,
                }
            except: pass
    return dmap


def extract_from_report(match_dir, date_dir, match_num):
    """从报告文件提取combo特征"""
    combos = {}
    # 报告文件在 date_dir 下，格式 周六030_xxx.md
    for f in glob.glob(os.path.join(date_dir, '周*' + match_num + '_*.md')):
        try:
            content = open(f, 'r', encoding='utf-8').read()
        except: continue

        # 欧赔盘路 - 从表格
        # | 竞彩官方 | x | y | z | a | b | c | ⬇⬆⬆ |
        om = re.search(r'竞彩官方\s*\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|\s*([⬇⬆⬉⬊➡→]+)', content)
        if om:
            ct = om.group(1).replace('⬇','降').replace('⬆','升').replace('➡','不变').replace('→','不变').replace('⬉','升').replace('⬊','降')
            combos['竞彩欧赔盘路'] = ct

        om = re.search(r'Interwetten\s*\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|\s*([⬇⬆⬉⬊➡→]+)', content)
        if om:
            ct = om.group(1).replace('⬇','降').replace('⬆','升').replace('➡','不变').replace('→','不变').replace('⬉','升').replace('⬊','降')
            combos['IW欧赔盘路'] = ct

        om = re.search(r'百家平均\s*\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|[\d.]+\|\s*([⬇⬆⬉⬊➡→]+)', content)
        if om:
            ct = om.group(1).replace('⬇','降').replace('⬆','升').replace('➡','不变').replace('→','不变').replace('⬉','升').replace('⬊','降')
            combos['百家欧赔盘路'] = ct

        # 澳门亚盘
        om = re.search(r'澳门亚盘[：:]\s*(.+)', content)
        if om:
            macau = om.group(1).strip()
            if macau != '未知':
                combos['澳门亚盘'] = macau

        # 各维度信号
        dim_map = {
            '欧赔趋势': '欧赔趋势_dir',
            '竞彩同赔': '欧赔趋势_dir',
            '澳门亚盘': '亚盘趋势_dir',
            '让球同赔': '让球趋势_dir',
            '主队主场': '主队主场_dir',
            '客队客场': '客队客场_dir',
            '百家对比': '百家对比_dir',
            '盘路匹配': '盘路匹配_dir',
            '庄家盈亏': '庄家盈亏_dir',
        }
        dp = r'\|(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|盘路匹配|庄家盈亏)\|([+-]?\d+\.\d+)\s*(利好主|利好客|中立)\s*\|'
        for m in re.finditer(dp, content):
            src = m.group(1)
            direction = m.group(3)
            score = m.group(2)
            dst = dim_map.get(src, src + '_dir')
            combos[dst] = direction
            combos[dst.replace('_dir', '_score')] = float(score)

        # 盘路匹配度
        om = re.search(r'盘路匹配度[：:]\s*(高|中|低)', content)
        if om:
            combos['盘路匹配'] = om.group(1)

    return combos


def extract_s25(dir_path):
    res = {}
    f = os.path.join(dir_path, 'step25_zhuangjia.json')
    if not os.path.exists(f): return res
    try:
        d = json.loads(open(f, 'r', encoding='utf-8').read())
        data = d.get('data', d)
        for r in ['主胜', '平局', '客胜']:
            if r in data:
                item = data[r]
                res[r + '_盈亏'] = '赢钱' if item.get('profit_dir') is True else ('亏钱' if item.get('profit_dir') is False else '')
                res[r + '_投注额'] = item.get('volume', '')
                res[r + '_占比'] = item.get('bet_pct', '')
        labels = d.get('labels', {})
        for key in ['主胜', '平局', '客胜']:
            if key in labels and labels[key].get('profit') in ['多', '中']:
                res['庄家方向'] = key; break
        for key in ['主胜', '平局', '客胜']:
            if key in labels and labels[key].get('bet_pct') == '多':
                res['大热方'] = key; break
    except: pass
    return res


def extract_s26(dir_path):
    res = {}
    f = os.path.join(dir_path, 'step26_profit_ratio.json')
    if not os.path.exists(f): return res
    try:
        d = json.loads(open(f, 'r', encoding='utf-8').read())
        analysis = d.get('analysis', {})
        for key in ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏']:
            val = analysis.get(key, '')
            res[key] = val
            if '赢' in val: res[key + '_方向'] = '正'
            elif '亏' in val: res[key + '_方向'] = '负'
        br = analysis.get('投注占比', {})
        if br:
            res['投注占比_主'] = br.get('胜', br.get('主', ''))
            res['投注占比_平'] = br.get('平', '')
            res['投注占比_客'] = br.get('负', br.get('客', ''))
        pr = analysis.get('盈亏占比', {})
        if pr:
            res['盈亏占比_主'] = pr.get('胜', pr.get('主', ''))
            res['盈亏占比_平'] = pr.get('平', '')
            res['盈亏占比_客'] = pr.get('负', pr.get('客', ''))
        if analysis.get('庄家最看好'):
            res['综合盈亏方向'] = analysis['庄家最看好']
    except: pass
    return res


def main():
    print('='*60)
    print('补全 feedback.json 特征数据 v2')
    print('='*60)

    # 1. 构建(date, match_num)映射
    print('[1/4] 构建目录映射...')
    dmap = build_dir_map()
    print('     找到 %d 个匹配项' % len(dmap))

    # 2. 加载feedback
    fb = json.loads(open(FEEDBACK_FILE, 'r', encoding='utf-8').read())
    dates = fb.get('dates', {})
    total = sum(len(v['feedback']) for v in dates.values())
    print('[2/4] feedback: %d天, %d场' % (len(dates), total))

    # 3. 补特征
    filled = 0
    skipped = 0
    for date, v in sorted(dates.items()):
        date_dir = os.path.join(TASKS_DIR, date)
        for f in v['feedback']:
            if f.get('s25'):
                skipped += 1
                continue
            mn = f['match_num']
            key = (date, mn)
            info = dmap.get(key)
            if not info:
                skipped += 1
                continue

            dp = info['dir']
            combos = extract_from_report(dp, date_dir, mn)
            s25 = extract_s25(dp)
            s26 = extract_s26(dp)

            if s25 or s26 or combos:
                f['combos'] = combos
                f['s25'] = s25
                f['s26'] = s26
                meta = info.get('meta', {})
                if meta.get('league'):
                    f['league'] = meta['league']
                filled += 1
            else:
                skipped += 1

    # 4. 保存
    fb['dates'] = dates
    stats = fb.get('stats', {})
    stats['total_matches'] = sum(len(v['feedback']) for v in dates.values())
    stats['total_correct'] = sum(1 for v in dates.values() for f in v['feedback'] if f.get('correct'))
    stats['overall_accuracy'] = round(stats['total_correct'] / stats['total_matches'], 4) if stats['total_matches'] else 0
    fb['stats'] = stats

    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)

    has_feat = sum(1 for v in dates.values() for f in v['feedback'] if f.get('s25'))
    print('\n[3/4] 结果:')
    print('     补特征: %d场' % filled)
    print('     跳过: %d场' % skipped)
    print('     现有特征: %d场' % has_feat)
    print('     总场次: %d' % stats['total_matches'])
    print('[4/4] 已保存')
    print('='*60)


if __name__ == '__main__':
    main()
