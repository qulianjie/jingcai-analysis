# -*- coding: utf-8 -*-
import sys, os, json, requests
from bs4 import BeautifulSoup
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0'})
sess.get('https://odds.500.com/', timeout=10)

data_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\data'
dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match')],
              key=lambda x: int(x.split('_')[0].replace('match','')))

for d in dirs:
    md = os.path.join(data_dir, d)
    mp = os.path.join(md, 'meta.json')
    if not os.path.exists(mp): continue
    with open(mp, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    fid = meta.get('fid', '')
    matchnum = meta.get('matchnum', d)
    if not fid: continue
    
    issues = []
    
    # Check step2 (ouzi)
    s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
    if os.path.exists(s2):
        with open(s2, 'r', encoding='utf-8') as f:
            sc = f.read()
        has_data = '共0' not in sc and len(sc) > 1500
        if not has_data:
            # Actually test AJAX
            try:
                resp = sess.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid, timeout=15)
                resp.encoding = 'gbk'
                soup = BeautifulSoup(resp.text, 'html.parser')
                jc = None
                for table in soup.find_all('table'):
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) < 12: continue
                        td0 = tds[0].get_text().strip()
                        if td0 == '1':
                            nums = []
                            for idx in [3,4,5,6,7,8]:
                                s = tds[idx].get_text().strip().replace(chr(160), '')
                                try: nums.append(float(s))
                                except: pass
                            if len(nums) >= 6:
                                jc = (nums[0],nums[1],nums[2])
                if jc:
                    ajax_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
                    referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=1&win=%.2f&draw=%.2f&lost=%.2f&fixtureid=%s' % (jc[0],jc[1],jc[2],fid)
                    h = {
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': referer,
                    }
                    params = {'cid': '1', 'win': '%.2f' % jc[0], 'draw': '%.2f' % jc[1], 'lost': '%.2f' % jc[2], 'id': fid, 'mid': '0'}
                    r2 = sess.get(ajax_url, params=params, headers=h, timeout=15)
                    try:
                        j = json.loads(r2.text)
                        count = sum(j.get('counts', [0,0,0]))
                        if count == 0:
                            issues.append('step2: 源站无同赔数据 (counts=%s)' % str(j.get('counts')))
                        else:
                            issues.append('step2: 源站有%d条，脚本提取失败!' % count)
                    except:
                        issues.append('step2: AJAX返回非JSON')
                else:
                    issues.append('step2: 页面找不到竞彩赔率')
            except Exception as e:
                issues.append('step2: 访问失败 %s' % str(e)[:50])
    
    # Check step5 (rangqiu)
    s5 = os.path.join(md, 'group02_handicap', 'step5_handicap_same.txt')
    if os.path.exists(s5):
        with open(s5, 'r', encoding='utf-8') as f:
            sc = f.read()
        has_data = '共0' not in sc and len(sc) > 1500
        if not has_data:
            # Actually test AJAX
            try:
                resp = sess.get('https://odds.500.com/fenxi/rangqiu-%s.shtml' % fid, timeout=15)
                resp.encoding = 'gbk'
                soup = BeautifulSoup(resp.text, 'html.parser')
                rq = None
                for table in soup.find_all('table'):
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) < 12: continue
                        td0 = tds[0].get_text().strip()
                        if td0 == '1':
                            nums = []
                            for idx in [4,5,6,7,8,9]:
                                s = tds[idx].get_text().strip().replace(chr(160), '')
                                try: nums.append(float(s))
                                except: pass
                            if len(nums) >= 6:
                                td2 = tds[2].get_text().strip().replace(chr(160), '')
                                rq = (td2, nums[0], nums[1], nums[2])
                if rq:
                    hd, win, draw, lost = rq
                    ajax_url = 'https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php'
                    referer = 'https://odds.500.com/fenxi1/rangqiu_same.php?cid=1&handicapline=%s&win=%.2f&draw=%.2f&lost=%.2f&id=%s' % (hd, win, draw, lost, fid)
                    h = {
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': referer,
                    }
                    params = {'cid': '1', 'handicapline': hd, 'win': '%.2f' % win, 'draw': '%.2f' % draw, 'lost': '%.2f' % lost, 'id': fid, 'mid': '0'}
                    r2 = sess.get(ajax_url, params=params, headers=h, timeout=15)
                    try:
                        j = json.loads(r2.text)
                        count = sum(j.get('counts', [0,0,0]))
                        if count == 0:
                            issues.append('step5: 源站无同赔数据 (counts=%s)' % str(j.get('counts')))
                        else:
                            issues.append('step5: 源站有%d条，脚本提取失败!' % count)
                    except:
                        issues.append('step5: AJAX返回非JSON或空响应')
                else:
                    issues.append('step5: 页面找不到让球赔率')
            except Exception as e:
                issues.append('step5: 访问失败 %s' % str(e)[:50])
    
    if issues:
        print('%s: %s' % (matchnum, ' | '.join(issues)))
    else:
        print('%s: OK' % matchnum)
