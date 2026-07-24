#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补全联赛缓存中缺失的竞彩官方(官*官*中国)公司行"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

SD = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def _odds_direction(init, live):
    d = ''
    for a, b in zip(init, live):
        if b > a + 0.01: d += '⬆'
        elif b < a - 0.01: d += '⬇'
        else: d += '➡'
    return d

def has_jingcai_company(m):
    """检查match的companies中是否已有竞彩官方"""
    oe = m.get('odds_europe', {})
    if not isinstance(oe, dict): return False
    for c in oe.get('companies', []):
        nm = c.get('name', '')
        if '官' in nm:
            return True
    return False

def fetch_jingcai_row(fid):
    """从500.com欧赔页提取竞彩官方行(第一行td0='1')"""
    if not fid: return None
    url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
    try:
        resp = sess.get(url, timeout=10)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                # 竞彩官方: td0='1' and 官 in name
                if td0 == '1' and '官' in td1:
                    nums = []
                    for idx in [3, 4, 5, 6, 7, 8]:
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(val))
                        except: break
                    if len(nums) >= 6:
                        return {
                            'name': td1,
                            'iw': nums[0], 'id': nums[1], 'il': nums[2],
                            'lw': nums[3], 'ld': nums[4], 'll': nums[5],
                            'dir': _odds_direction(nums[:3], nums[3:6])
                        }
        return None
    except:
        return None

def fix_cache(cache_path):
    """修复单个缓存文件"""
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    league = os.path.basename(cache_path).replace('.json', '')
    ml = data.get('all_matches', [])
    
    # 找出缺竞彩官方的比赛
    to_fix = []
    for m in ml:
        fid = str(m.get('FIXTUREID', ''))
        if not fid: continue
        if not has_jingcai_company(m):
            # 检查是否有 odds_europe (有数据才需要修复)
            oe = m.get('odds_europe')
            if isinstance(oe, dict) and oe.get('companies'):
                to_fix.append((fid, m))
    
    print(f'[{league}] {len(to_fix)}/{len(ml)} 场缺竞彩官方')
    if not to_fix:
        return 0, 0
    
    fixed = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        fut_map = {pool.submit(fetch_jingcai_row, fid): (fid, m) for fid, m in to_fix}
        for fut in as_completed(fut_map):
            fid, m = fut_map[fut]
            try:
                jc_row = fut.result()
            except:
                jc_row = None
            if jc_row:
                oe = m.get('odds_europe', {})
                if isinstance(oe, dict):
                    cs = oe.get('companies', [])
                    cs.insert(0, jc_row)  # 插到最前面
                    oe['companies'] = cs
                    fixed += 1
    return fixed, len(to_fix)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print('用法: python _fix_jingcai_company.py 巴甲.json 欧罗巴.json [--save]')
        sys.exit(1)
    
    do_save = '--save' in args
    files = [a for a in args if a != '--save']
    
    for fn in files:
        fp = os.path.join(CACHE_DIR, fn)
        if not os.path.exists(fp):
            print(f'文件不存在: {fp}')
            continue
        print(f'\n处理: {fn}')
        fixed, total = fix_cache(fp)
        if fixed > 0 and do_save:
            # 重新保存
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with open(fp + '.bak', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            print(f'  已保存 (备份: {fn}.bak)')
        
        summary = f'{fn}: 修复{fixed}/{total}场'
        print(f'  {summary}')
        with open(os.path.join(SD, '_fix_jc_company.log'), 'a') as lf:
            lf.write(summary + '\n')
    
    if not do_save:
        print('\n⚠️ 未保存(--save才会写回文件)。先跑预览确认数量正确')
