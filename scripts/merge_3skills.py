# -*- coding: utf-8 -*-
"""
竞彩全skill 合并提示：解析 4way / min / samepan / jc_sameodds / av_sameodds
五个工具的输出文件，每场合成一个方向信号（多数投票），输出提示 + 各工具分布。

用法:
  python.exe scripts/merge_3skills.py 2026-08-15 [--out C:/path/out.txt]
默认找 workspace 根 4way_{date}.txt / min_{date}.txt；
samepan / sameodds(jc) / av_sameodds 在 jingcai_out。
"""
import re, sys, os

def load(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return f.read()

def parse_dist(s):
    """'主胜:3(33%)|平局:1(11%)|客胜:5(55%)' 或 4way 无括号格式 '客胜:1(33%)|平:2(66%)' -> {'主胜':n,'平':n,'客胜':n}"""
    d = {}
    for m in re.finditer(r'(主胜|平局|平|客胜):(\d+)', s):
        col = '平' if m.group(1) in ('平局', '平') else m.group(1)
        d[col] = int(m.group(2))
    return d

def direction(dist, min_n=2):
    """分布多数列；总样本 < min_n 返回 None（无有效方向）"""
    if not dist or sum(dist.values()) < min_n:
        return None
    return max(dist, key=dist.get)

def pct(dist, col):
    t = sum(dist.values())
    if t == 0:
        return '0%'
    return '%d%%' % round(dist.get(col, 0) * 100.0 / t)

def fmt_dist(dist):
    if not dist or sum(dist.values()) == 0:
        return '0场'
    n = sum(dist.values())
    s = '主胜%d(%s)' % (dist.get('主胜', 0), pct(dist, '主胜'))
    s += '|平%d(%s)' % (dist.get('平', 0), pct(dist, '平'))
    s += '|客胜%d(%s)' % (dist.get('客胜', 0), pct(dist, '客胜'))
    return '%d场 %s' % (n, s)

# ---------------- 解析五个工具输出 ----------------

def parse_4way(txt):
    """编号 -> {'teams','fid','n','dist'}。标题行在文件头集中，块1..N 对应场次1..N。
    支持子集输出（如只跑 006-016）：块按标题出现顺序与标题序号 zip 映射。"""
    title_matches = list(re.finditer(r'^\[(\d+)/(\d+)\]\s*(.+?)\s+FID=(\d+).*?→\s*(\d+)场', txt, re.M))
    idxs = [int(m.group(1)) for m in title_matches]
    titles = {}
    for m in title_matches:
        titles[int(m.group(1))] = {'teams': m.group(3).strip(), 'fid': m.group(4), 'n': int(m.group(5))}
    blocks = re.split(r'\r?\n═+\r?\n', txt)
    out = {}
    for bi, idx in enumerate(idxs, 1):  # 第 bi 个块 ↔ 标题列表第 bi 个序号
        if bi >= len(blocks):
            break
        b = blocks[bi]
        dm = re.search(r'^\s*📊\s*(\d+)场(.*)$', b, re.M)
        out[idx] = {'dist': parse_dist(dm.group(2)) if dm else {}}
    for k, v in titles.items():
        if k not in out:
            out[k] = {'dist': {}}
        out[k]['teams'] = v['teams']
        out[k]['fid'] = v['fid']
        out[k]['n'] = v['n']
    return out

def parse_min(txt):
    """编号 -> {'teams','fid','dist'}。标题行直接跟详情块"""
    blocks = re.split(r'(?m)^(?=\[\d+/)', txt)
    out = {}
    for b in blocks:
        m = re.search(r'^\[(\d+)/(\d+)\]\s*(.+?)\s+FID=(\d+)', b, re.M)
        if not m:
            continue
        idx = int(m.group(1))
        dm = re.search(r'^\s*📊\s*(\d+)场（(.*?)）', b, re.M)
        out[idx] = {'teams': m.group(3).strip(),
                    'fid': m.group(4),
                    'dist': parse_dist(dm.group(2)) if dm else {}}
    return out

def parse_samepan(txt):
    """'周一001' -> {'teams','home','away'}。home/away 为 {'主胜','平','客胜'} 计数"""
    blocks = re.split(r'(?m)^(?=\[周[一二三四五六日]\d+\])', txt)
    out = {}
    for b in blocks:
        m = re.search(r'^\[(周[一二三四五六日]\d+)\]\s*(.+?)\s*\(', b, re.M)
        if not m:
            continue
        no = m.group(1)
        home = re.search(r'^\s*主队\s+\S+ \(主场\+同盘\)\s+(\d+)场\s+主胜(\d+)\s+平(\d+)\s+客胜(\d+)', b, re.M)
        away = re.search(r'^\s*客队\s+\S+ \(客场\+同盘\)\s+(\d+)场\s+主胜(\d+)\s+平(\d+)\s+客胜(\d+)', b, re.M)
        e = {'teams': m.group(2).strip(), 'home': None, 'away': None}
        if home:
            e['home'] = {'主胜': int(home.group(2)), '平': int(home.group(3)), '客胜': int(home.group(4))}
        if away:
            e['away'] = {'主胜': int(away.group(2)), '平': int(away.group(3)), '客胜': int(away.group(4))}
        out[no] = e
    return out

def parse_sameodds(txt):
    """jc_sameodds / av_sameodds 输出: '【周六001】队 vs 队（联赛）FID=xxx' + 相同联赛统计分布
    -> {'周六001': {'teams','fid','dist'}}  dist 为 {'主胜','平','客胜'} 计数
    只取「一、相同联赛」统计；该区无命中(0场)则 dist 为空。
    """
    blocks = re.split(r'(?m)^(?=【周[一二三四五六日]\d+】)', txt)
    out = {}
    for b in blocks:
        m = re.search(r'^【(周[一二三四五六日]\d+)】\s*(.+?)\s*FID=(\d+)', b, re.M)
        if not m:
            continue
        no = m.group(1)
        # 相同联赛统计行: 📊 相同联赛统计（日职）：胜1 平0 负0（共1场），胜率100.0%
        dm = re.search(r'📊\s*相同联赛统计（[^）]*）：胜(\d+)\s+平(\d+)\s+负(\d+)（共(\d+)场）', b)
        dist = {}
        if dm and int(dm.group(4)) > 0:
            dist = {'主胜': int(dm.group(1)), '平': int(dm.group(2)), '客胜': int(dm.group(3))}
        out[no] = {'teams': m.group(2).strip(), 'fid': m.group(3), 'dist': dist}
    return out

# ---------------- 场次对齐 ----------------

def team_key(s):
    return re.sub(r'\s+', '', s)

def align(fw, mn, sp, jc, av):
    """4way/min 数字编号 -> samepan/jc/av 周Xnnn 编号。
    samepan 按主队名匹配；jc/av 优先按 FID 精确匹配，失败退回主队名。"""
    sp_by_team = {team_key(v['teams']): k for k, v in sp.items()}
    # jc/av 的 teams 形如 '福冈黄蜂 vs 水户蜀葵（日职）'，去（联赛）后缀后与 4way/min 同名
    def _clean(t):
        return re.sub(r'[（(].*?[）)]$', '', t).strip()
    jc_by_fid = {v['fid']: k for k, v in jc.items() if v.get('fid')}
    av_by_fid = {v['fid']: k for k, v in av.items() if v.get('fid')}
    jc_by_team = {team_key(_clean(v['teams'])): k for k, v in jc.items()}
    av_by_team = {team_key(_clean(v['teams'])): k for k, v in av.items()}
    merged = []
    for idx in sorted(fw.keys()):
        f = fw.get(idx, {})
        m = mn.get(idx, {})
        tk = team_key(f.get('teams', m.get('teams', '')))
        fid = f.get('fid') or m.get('fid')
        sp_no = None
        if tk in sp_by_team:
            sp_no = sp_by_team[tk]
        else:
            for stk, sno in sp_by_team.items():
                if tk and (tk in stk or stk in tk):
                    sp_no = sno
                    break
        # jc/av 对齐：FID 优先
        jc_no = jc_by_fid.get(fid) if fid else None
        if not jc_no and tk in jc_by_team:
            jc_no = jc_by_team[tk]
        if not jc_no:
            for stk, sno in jc_by_team.items():
                if tk and (tk in stk or stk in tk):
                    jc_no = sno
                    break
        av_no = av_by_fid.get(fid) if fid else None
        if not av_no and tk in av_by_team:
            av_no = av_by_team[tk]
        if not av_no:
            for stk, sno in av_by_team.items():
                if tk and (tk in stk or stk in tk):
                    av_no = sno
                    break
        merged.append({
            'idx': idx, 'teams': f.get('teams') or m.get('teams', ''),
            'fw': f, 'mn': m,
            'sp': sp.get(sp_no, {}) if sp_no else {},
            'sp_no': sp_no,
            'jc': jc.get(jc_no, {}) if jc_no else {},
            'jc_no': jc_no,
            'av': av.get(av_no, {}) if av_no else {},
            'av_no': av_no,
        })
    return merged

# ---------------- 合成信号 ----------------

def merge_signal(row):
    votes = []
    detail = []
    for name, dist in (('min', row['mn'].get('dist', {})),
                        ('4way', row['fw'].get('dist', {}))):
        d = direction(dist)
        detail.append((name, d, dist))
        if d:
            votes.append(d)
    for name, dist in (('jc', row['jc'].get('dist', {})),
                       ('av', row['av'].get('dist', {}))):
        d = direction(dist)
        detail.append((name, d, dist))
        if d:
            votes.append(d)
    for name, dist in (('主队线', row['sp'].get('home')),
                       ('客队线', row['sp'].get('away'))):
        d = direction(dist)
        detail.append((name, d, dist))
        if d:
            votes.append(d)
    cnt = {}
    for v in votes:
        cnt[v] = cnt.get(v, 0) + 1
    n = len(votes)
    if n == 0:
        return None, '—', votes, detail
    best = max(cnt, key=cnt.get)
    bcnt = cnt[best]
    others = sum(c for k, c in cnt.items() if k != best)
    if bcnt == n:  # 全部同向
        if n >= 4:
            flag = '🔥强'
        elif n == 3:
            flag = '✅'
        elif n == 2:
            flag = '⚠️偏'
        else:
            flag = '⚠️单源'
    elif bcnt >= 2 and others <= 1:
        flag = '⚠️偏'
    else:
        flag = '❌分散'
    return best, flag, votes, detail

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else '2026-08-15'
    d = date.replace('-', '')
    # --range 支持（任意位置；优先读 range 版输出文件 *_NNN-NNN.txt）
    rng = ''
    if '--range' in sys.argv:
        ri = sys.argv.index('--range')
        if ri + 1 < len(sys.argv):
            rng = sys.argv[ri + 1]
    suf = ('_' + rng) if rng else ''
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = 'C:/Users/lianjie/jingcai_out'

    def _first(paths):
        return next((p for p in paths if os.path.exists(p)), paths[0])

    fw_path = _first([
        os.path.join(base, '..', '4way_%s%s.txt' % (date, suf)),
        os.path.join(base, '..', '4way_%s.txt' % date),
    ])
    mn_path = _first([
        os.path.join(base, '..', 'min_%s%s.txt' % (date, suf)),
        os.path.join(base, '..', 'min_%s.txt' % date),
    ])
    sp_candidates = [
        os.path.join(out_dir, 'samepan_%s%s.txt' % (date, suf)),
        os.path.join(base, '..', 'samepan_%s.txt' % d),
        os.path.join(base, '..', 'samepan_%s.txt' % date),
        os.path.join(out_dir, 'samepan_%s.txt' % date),
        os.path.join(out_dir, 'samepan_%s.txt' % d),
    ]
    sp_path = _first(sp_candidates)
    jc_path = _first([
        os.path.join(out_dir, 'sameodds_%s%s.txt' % (date, suf)),
        os.path.join(out_dir, 'sameodds_%s.txt' % date),
    ])
    av_path = _first([
        os.path.join(out_dir, 'av_sameodds_%s%s.txt' % (date, suf)),
        os.path.join(out_dir, 'av_sameodds_%s.txt' % date),
    ])
    if not os.path.exists(fw_path):
        # 允许传自定义路径
        fw_path = sys.argv[2] if len(sys.argv) > 2 else fw_path
    print('解析: %s' % fw_path, file=sys.stderr)
    fw = parse_4way(load(fw_path))
    mn = parse_min(load(mn_path))
    sp = parse_samepan(load(sp_path))
    jc = parse_sameodds(load(jc_path)) if os.path.exists(jc_path) else {}
    av = parse_sameodds(load(av_path)) if os.path.exists(av_path) else {}
    print('4way %d场, min %d场, samepan %d场, jc %d场, av %d场' % (len(fw), len(mn), len(sp), len(jc), len(av)), file=sys.stderr)

    rows = align(fw, mn, sp, jc, av)
    if rng:
        rm = re.match(r'^\s*(\d+)\s*-\s*(\d+)\s*$', rng)
        if rm:
            lo, hi = int(rm.group(1)), int(rm.group(2))
            rows = [r for r in rows if lo <= r['idx'] <= hi]
    out = []
    out.append('⚽ 竞彩全skill 合成信号 %s' % date)
    out.append('  工具: min 4way jc av samepan(主/客队线)')
    out.append('')
    for r in rows:
        best, flag, votes, detail = merge_signal(r)
        line = '[%02d] %s' % (r['idx'], r['teams'])
        out.append(line)
        for name, d, dist in detail:
            if dist:
                out.append('  %-4s %s %s' % (name, fmt_dist(dist), ('方向:' + d) if d else '样本少'))
            else:
                out.append('  %-4s 无匹配' % name)
        if best:
            out.append('  合成: %s %s (票:%s)' % (flag, best, '+'.join(votes)))
        else:
            out.append('  合成: — 无有效信号')
        out.append('')
    text = '\n'.join(out)
    print(text)
    if '--out' in sys.argv:
        oi = sys.argv.index('--out')
        with open(sys.argv[oi + 1], 'w', encoding='utf-8') as f:
            f.write(text)

if __name__ == '__main__':
    main()
