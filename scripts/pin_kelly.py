# -*- coding: utf-8 -*-
"""Pinnacle(平博) 凯利值筛选：返还率 >90% 且 凯利指数 >1
用法: python pin_kelly.py [date]   (默认今天)
"""
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _http_common

DATE = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y-%m-%d')
SD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(SD, 'tasks', DATE, 'matches_data.json')

with open(MD, encoding='utf-8') as f:
    md = json.load(f)

matches = []
for g, v in md.get('groups', {}).items():
    for m in v.get('matches', []):
        matches.append(m)

print('📅 %s  共 %d 场 — Pinnacle 凯利筛选（返还率>90%% 且 凯利>1）\n' % (DATE, len(matches)))

HITS = []
HITSI = []
ROWS = []

for i, m in enumerate(matches, 1):
    fid = m.get('fid', '')
    home, away = m.get('home', '?'), m.get('away', '?')
    num = m.get('matchnum', '?')
    try:
        h = _http_common.headers()
        h['Accept-Encoding'] = 'identity'
        r = requests.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid, headers=h, timeout=25)
        r.encoding = 'gbk'
        if len(r.text) < 5000:
            print('[%02d] %-14s %s vs %s — 抓取被拦' % (i, num, home, away))
            time.sleep(1.2)
            continue
        s = BeautifulSoup(r.text, 'html.parser')
        pin = None
        for tr in s.find_all('tr'):
            tds = [t.get_text(' ', strip=True) for t in tr.find_all('td')]
            if len(tds) >= 27 and '(荷兰)' in tds[1] and 'P' in tds[1]:
                pin = tds
                break
        if not pin:
            print('[%02d] %-14s %s vs %s — 未找到 Pinnacle' % (i, num, home, away))
            time.sleep(1.2)
            continue
        init_odds = [pin[3], pin[4], pin[5]]
        live_odds = [pin[6], pin[7], pin[8]]
        ret_i, ret_l = pin[17], pin[18]
        kel_i = [pin[20], pin[21], pin[22]]
        kel_l = [pin[23], pin[24], pin[25]]
        rl = float(ret_l.replace('%', ''))
        ri_f = float(ret_i.replace('%', ''))
        labels = ['胜', '平', '负']
        hits = []
        for j, k in enumerate(kel_l):
            kv = float(k)
            if rl > 90 and kv > 1.0:
                hits.append((labels[j], kv))
        hits_i = []
        for j, k in enumerate(kel_i):
            kv = float(k)
            if ri_f > 90 and kv > 1.0:
                hits_i.append((labels[j], kv))
        ROWS.append((num, home, away, ret_i, ret_l, kel_i, kel_l, live_odds))
        if hits or hits_i:
            HITS.append((num, home, away, rl, hits))
            if hits_i:
                HITSI.append((num, home, away, ret_i, hits_i))
            tag = ''
            if hits:
                tag += ' ⟵ 终 ✅ %s' % ' + '.join('%s %.2f' % (d, v) for d, v in hits)
            if hits_i:
                tag += ' ⟵ 初 ✅ %s' % ' + '.join('%s %.2f' % (d, v) for d, v in hits_i)
            print('[%02d] %-14s %s vs %s  返还 初%s/终%s  凯利 初 %s | 终 %s%s' % (
                i, num, home, away, ret_i, ret_l,
                '/'.join(kel_i), '/'.join(kel_l), tag))
        else:
            print('[%02d] %-14s %s vs %s  返还 %s  凯利 %s' % (i, num, home, away, ret_l, '/'.join(kel_l)))
    except Exception as e:
        print('[%02d] %-14s %s vs %s — ERR %s' % (i, num, home, away, str(e)[:50]))
    time.sleep(1.2)

_hits_by_num = {h[0]: h[4] for h in HITS}
n_live = sum(1 for h in HITS if h[4])
print('\n' + '=' * 60)
print('🎯 终盘命中（终盘返还率>90%% 且 终盘凯利>1）：%d 场' % n_live)
for num, home, away, rl, hits in HITS:
    for d, v in hits:
        print('  %s  %s vs %s → %s  凯利=%.2f  返还率=%s' % (num, home, away, d, v, rl))
print('\n🎯 初盘命中（初盘返还率>90%% 且 初盘凯利>1）：%d 场 / %d 个方向' % (len(HITSI), sum(len(x[4]) for x in HITSI)))
for num, home, away, ri, hits_i in HITSI:
    for d, v in hits_i:
        print('  %s  %s vs %s → %s  凯利=%.2f  返还率=%s' % (num, home, away, d, v, ri))
only_i = [x for x in HITSI if not _hits_by_num.get(x[0])]
print('\n⚠️ 仅初盘命中（终盘已回落<1）：%d 场' % len(only_i))
for num, home, away, ri, hits_i in only_i:
    print('  %s  %s vs %s → %s' % (num, home, away, ' + '.join('%s %.2f' % (d, v) for d, v in hits_i)))

def _outdir():
    """自适应输出目录：Windows Python 用 C:\\，WSL python3 用 /mnt/c/"""
    for c in (r'C:\Users\lianjie\jingcai_out', '/mnt/c/Users/lianjie/jingcai_out'):
        if os.path.isdir(c):
            return c
    os.makedirs('/mnt/c/Users/lianjie/jingcai_out', exist_ok=True)
    return '/mnt/c/Users/lianjie/jingcai_out'


outp = os.path.join(_outdir(), 'pin_kelly_%s.txt' % DATE)
with open(outp, 'w', encoding='utf-8') as f:
    f.write('Pinnacle 凯利筛选 %s（返还率>90%% 且 凯利>1）\n\n' % DATE)
    for num, home, away, ri, rl, ki, kl, lo in ROWS:
        f.write('%s %s vs %s\n' % (num, home, away))
        f.write('  终赔 胜%s 平%s 负%s   返还 初%s 终%s\n' % (lo[0], lo[1], lo[2], ri, rl))
        f.write('  凯利 初 %s/%s/%s  终 %s/%s/%s\n\n' % (ki[0], ki[1], ki[2], kl[0], kl[1], kl[2]))
    f.write('\n终盘命中 %d 场:\n' % n_live)
    for num, home, away, rl, hits in HITS:
        for d, v in hits:
            f.write('  %s %s vs %s → %s 凯利=%.2f 返还率=%s\n' % (num, home, away, d, v, rl))
    f.write('\n初盘命中 %d 场:\n' % len(HITSI))
    for num, home, away, ri, hits_i in HITSI:
        for d, v in hits_i:
            f.write('  %s %s vs %s → %s 凯利=%.2f 返还率=%s\n' % (num, home, away, d, v, ri))
    f.write('\n仅初盘命中(终盘回落<1) %d 场:\n' % len(only_i))
    for num, home, away, ri, hits_i in only_i:
        f.write('  %s %s vs %s → %s\n' % (num, home, away, ' + '.join('%s %.2f' % (d, v) for d, v in hits_i)))
print('\n[FILE] %s' % outp)
