# -*- coding: utf-8 -*-
"""
4skill 交付一致性检查 (2026-09-05 用户要求"加个检查")
=====================================================
1. 文件同源检查: merge 读 workspace 根 4way/min, make_docx 读 jingcai_out。
   两处内容不一致(md5) = merge 合成段与 docx 明细段不同源 (已踩坑2次!)
2. 数据时点标注: 除 jc_sameodds(竞彩同赔=官方初盘, 初盘确定后不变) 外,
   4way/min/av/samepan 都吃实时/终盘数据 -> 标注抓取时点供时效核对。
3. 场次匹配数抽查: merge 中 4way N场 vs 明细标题行 '→ N场' 是否一致。

用法: python check_4skill_consistency.py 2026-09-05
"""
import os, re, sys, datetime, hashlib

WS = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
OUT = r'C:\Users\lianjie\jingcai_out'

def md5(path):
    try:
        h = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()[:10]
    except OSError:
        return None

def mtime(path):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path))
    except OSError:
        return None

def main():
    date = sys.argv[1] if len(sys.argv) > 1 else '2026-09-05'
    print(f'===== 4skill 一致性检查 {date} =====')
    print()
    print('--- 1. 文件同源 (merge读workspace根 / docx明细读jingcai_out) ---')
    for tag, fname in (('4way', f'4way_{date}.txt'), ('min ', f'min_{date}.txt')):
        a, b = md5(f'{WS}\\{fname}'), md5(f'{OUT}\\{fname}')
        ta, tb = mtime(f'{WS}\\{fname}'), mtime(f'{OUT}\\{fname}')
        if a is None or b is None:
            print(f'🚨 {tag}: 文件缺失 (ws={a is not None} out={b is not None})')
        elif a == b:
            print(f'✅ {tag}: 内容一致 md5={a} (ws {ta:%H:%M:%S} / out {tb:%H:%M:%S})')
        else:
            print(f'🚨 {tag}: 不同源! ws md5={a} vs out md5={b} — merge与docx明细会不一致! 需 cp 同步')
    print()
    print('--- 2. 数据时点 (除 jc 同赔=官方初盘固定外, 其余需时效核对) ---')
    now = datetime.datetime.now()
    tools = [
        ('4way(实时亚盘+欧赔)', f'{OUT}\\4way_{date}.txt', True),
        ('min(实时欧赔)',       f'{OUT}\\min_{date}.txt', True),
        ('samepan(实时亚盘匹配)', f'{OUT}\\samepan_{date}.txt', True),
        ('jc 同赔(官方初盘)',   f'{OUT}\\sameodds_{date}.txt', False),
        ('av 同赔(实时终盘)',   f'{OUT}\\av_sameodds_{date}.txt', True),
    ]
    for tag, path, need_chk in tools:
        t = mtime(path)
        if t is None:
            print(f'  {tag:22s} 缺失!')
            continue
        age = (now - t).total_seconds() / 60
        if need_chk and age > 30:
            warn = f' 🚨 {age:.0f}分钟前抓取, 临场可能已变!'
        elif need_chk:
            warn = f' (抓取于 {age:.0f}分钟前)'
        else:
            warn = ' (初盘固定, 无需时效核对)'
        print(f'  {tag:22s} {t:%H:%M:%S}{warn}')
    print()
    print('--- 3. merge 4way 场数 vs 明细标题 → N场 (抽查) ---')
    try:
        mtxt = open(f'{OUT}\\merge_{date}.txt', encoding='utf-8').read()
        ftxt = open(f'{OUT}\\4way_{date}.txt', encoding='utf-8').read()
    except OSError as e:
        print('  读取失败:', e); return 1
    fw_title = {}
    for m in re.finditer(r'^\[(\d+)/(\d+)\]\s*(.+?)\s+FID=\d+.*?→\s*(\d+)场', ftxt, re.M):
        fw_title[int(m.group(1))] = int(m.group(4))
    blocks = re.split(r'(?m)^(?=\[\d{2}\] )', mtxt)
    bad = 0
    for b in blocks:
        tm = re.match(r'^\[(\d{2})\] ', b)
        if not tm:
            continue
        idx = int(tm.group(1))
        mm = re.search(r'^  4way\s*(?:(\d+)场|无匹配)', b, re.M)
        mv = int(mm.group(1)) if mm and mm.group(1) else 0
        fv = fw_title.get(idx, -1)
        if mv != fv:
            bad += 1
            print(f'  🚨 [{idx:02d}] merge 4way={mv}场 vs 明细标题={fv}场 不一致!')
    if bad == 0:
        print('  ✅ 全部场次 merge 4way 场数与明细一致')
    return 0 if bad == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
