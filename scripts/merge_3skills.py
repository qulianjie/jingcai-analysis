# -*- coding: utf-8 -*-
"""
竞彩3skill 合并提示：解析 4way / min / samepan 三个工具的输出文件，
每场合成一个方向信号（多数投票），输出一行提示 + 三个工具各自分布。

用法:
  python.exe scripts/merge_3skills.py 2026-08-15 [--out C:/path/out.txt]
默认找同目录 4way_{date}.txt / min_{date}.txt / samepan_{date_无横线}.txt
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

# ---------------- 解析三个工具输出 ----------------

def parse_4way(txt):
    """编号 -> {'teams','n','dist'}。标题行在文件头集中，块1..N 对应场次1..N"""
    titles = {}
    for m in re.finditer(r'^\[(\d+)/(\d+)\]\s*(.+?)\s+FID=.*?→\s*(\d+)场', txt, re.M):
        titles[int(m.group(1))] = {'teams': m.group(3).strip(), 'n': int(m.group(4))}
    blocks = re.split(r'\r?\n═+\r?\n', txt)
    out = {}
    for i, b in enumerate(blocks):
        if i == 0:
            continue
        dm = re.search(r'^\s*📊\s*(\d+)场(.*)$', b, re.M)
        if dm:
            out[i] = {'dist': parse_dist(dm.group(2))}
    for k, v in titles.items():
        if k not in out:
            out[k] = {'dist': {}}
        out[k]['teams'] = v['teams']
        out[k]['n'] = v['n']
    return out

def parse_min(txt):
    """编号 -> {'teams','dist'}。标题行直接跟详情块"""
    blocks = re.split(r'(?m)^(?=\[\d+/)', txt)
    out = {}
    for b in blocks:
        m = re.search(r'^\[(\d+)/(\d+)\]\s*(.+?)\s+FID=', b, re.M)
        if not m:
            continue
        idx = int(m.group(1))
        dm = re.search(r'^\s*📊\s*(\d+)场（(.*?)）', b, re.M)
        out[idx] = {'teams': m.group(3).strip(),
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

# ---------------- 场次对齐（按队名） ----------------

def team_key(s):
    return re.sub(r'\s+', '', s)

def align(fw, mn, sp):
    """4way/min 数字编号 -> samepan 周Xnnn 编号，按主队名匹配"""
    sp_by_team = {team_key(v['teams']): k for k, v in sp.items()}
    merged = []
    for idx in sorted(fw.keys()):
        f = fw.get(idx, {})
        m = mn.get(idx, {})
        tk = team_key(f.get('teams', m.get('teams', '')))
        sp_no = None
        if tk in sp_by_team:
            sp_no = sp_by_team[tk]
        else:
            # 模糊：主队名子串匹配
            for stk, sno in sp_by_team.items():
                if tk and (tk in stk or stk in tk):
                    sp_no = sno
                    break
        merged.append({
            'idx': idx, 'teams': f.get('teams') or m.get('teams', ''),
            'fw': f, 'mn': m,
            'sp': sp.get(sp_no, {}) if sp_no else {},
            'sp_no': sp_no,
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
    base = os.path.dirname(os.path.abspath(__file__))
    fw_path = os.path.join(base, '..', '4way_%s.txt' % date)
    mn_path = os.path.join(base, '..', 'min_%s.txt' % date)
    # samepan 命名可能带/不带横线，位置可能在 workspace 根或 jingcai_out
    sp_candidates = [
        os.path.join(base, '..', 'samepan_%s.txt' % d),
        os.path.join(base, '..', 'samepan_%s.txt' % date),
        os.path.join('C:/Users/lianjie/jingcai_out', 'samepan_%s.txt' % date),
    ]
    sp_path = next((p for p in sp_candidates if os.path.exists(p)), sp_candidates[0])
    if not os.path.exists(fw_path):
        # 允许传自定义路径
        fw_path = sys.argv[2] if len(sys.argv) > 2 else fw_path
    print('解析: %s' % fw_path, file=sys.stderr)
    fw = parse_4way(load(fw_path))
    mn = parse_min(load(mn_path))
    sp = parse_samepan(load(sp_path))
    print('4way %d场, min %d场, samepan %d场' % (len(fw), len(mn), len(sp)), file=sys.stderr)

    rows = align(fw, mn, sp)
    out = []
    out.append('⚽ 竞彩3skill 合成信号 %s' % date)
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
