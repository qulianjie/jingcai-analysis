# -*- coding: utf-8 -*-
"""修复 meta.json 中的空 league 和 macau_line"""
import os, json, re, requests
from bs4 import BeautifulSoup

# fid=1411377 的比赛
fid = '1411377'
meta_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data\match4_赫罗纳__皇家社会\meta.json'

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# 从 odds.500.com 获取联赛名
print(f"从 odds.500.com 获取 fid={fid} 的联赛信息...")
try:
    url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 查找 data-simpleleague 属性
    league_name = ''
    home_name = ''
    away_name = ''
    
    # 方法1: 从页面提取比赛信息
    for div in soup.find_all('div'):
        league = div.get('data-simpleleague', '')
        if league:
            league_name = league
            break
    
    # 方法2: 从标题提取
    if not league_name:
        title = soup.title.get_text() if soup.title else ''
        print(f"页面标题: {title}")
    
    # 从 yazhi 页面获取 macau_line 和球队名
    macau_line = ''
    home_id = ''
    away_id = ''
    
    try:
        url_yz = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
        resp_yz = sess.get(url_yz, timeout=15)
        resp_yz.encoding = 'gbk'
        soup_yz = BeautifulSoup(resp_yz.text, 'html.parser')
        
        for table in soup_yz.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 10: continue
                
                name = tds[1].get_text().strip()
                if '澳门' in name:
                    # 提取盘口
                    for idx in [3, 4, 5, 10, 11]:
                        if idx < len(tds):
                            val = tds[idx].get_text().strip().replace('\u00a0', '')
                            if any(c in val for c in ['让', '球', '半', '盘', '受让']):
                                val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                                val = re.sub(r'[\d\.]+', '', val).strip()
                                val = val.replace('升', '').replace('降', '').strip()
                                if val:
                                    macau_line = val
                                    break
                    if macau_line: break
        
        if not macau_line:
            # 从第一行提取
            for table in soup_yz.find_all('table'):
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) < 10: continue
                    td0 = tds[0].get_text().strip()
                    if td0 in ['1', '2', '3']:
                        for idx in range(len(tds)):
                            val = tds[idx].get_text().strip().replace('\u00a0', '')
                            if any(c in val for c in ['让', '球', '半', '受让']) and not val.isdigit():
                                val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                                val = re.sub(r'[\d\.]+', '', val).strip()
                                val = val.replace('升', '').replace('降', '').strip()
                                if val:
                                    macau_line = val
                                    break
                        if macau_line: break
                if macau_line: break
    except Exception as e:
        print(f"yazhi 页面获取失败: {e}")
    
    # 更新 meta.json
    print(f"获取结果:")
    print(f"  league={repr(league_name)}")
    print(f"  macau_line={repr(macau_line)}")
    
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        if league_name:
            meta['league'] = league_name
        if macau_line:
            meta['macau_line'] = macau_line
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        print(f"meta.json 已更新")
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        print(f"meta.json 不存在: {meta_path}")

except Exception as e:
    print(f"获取失败: {e}")
