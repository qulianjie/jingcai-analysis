# -*- coding: utf-8 -*-
"""
从odds.500.com的亚盘页面提取主队/客队team_id和澳门盘口信息
用法: python extract_team_info.py <fid> <league>
输出JSON到stdout: {"home_id":"xxx","away_id":"xxx","macau_line":"xxx","home_name":"xxx","away_name":"xxx"}
"""
import sys, os, json, re
import requests
from bs4 import BeautifulSoup

FID = sys.argv[1] if len(sys.argv) > 1 else ''
LEAGUE = sys.argv[2] if len(sys.argv) > 2 else ''

if not FID:
    print(json.dumps({'error': 'FID required'}))
    sys.exit(1)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

sess = requests.Session()
sess.headers.update(HEADERS)

result = {'home_id': '', 'away_id': '', 'macau_line': '', 'home_name': '', 'away_name': '', 'macau_ih': '', 'macau_il': ''}

# 从亚盘页面提取信息
try:
    url = 'https://odds.500.com/fenxi/yazhi-{}.shtml'.format(FID)
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # 提取比赛名称（标题中）
    title = soup.find('title')
    if title:
        title_text = title.get_text().strip()
        # 格式通常为: "fid_主队vs客队_亚盘" 或类似
        # 尝试从页面内容提取
        pass
    
    # 从亚盘表格提取澳门数据
    # 澳门通常在row #2
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12:
                continue
            td0 = tds[0].get_text().strip()
            td1 = tds[1].get_text().strip()
            
            # 找澳门 (row 2) 或通过名称匹配
            is_macau = False
            if td0 == '2':
                is_macau = True
            elif '澳门' in td1 or '门' in td1:
                is_macau = True
            
            if is_macau:
                # td[4]=即时盘口, td[3]=即时主队水位, td[5]=即时客队水位
                # td[10]=初盘盘口, td[9]=初盘主队水位, td[11]=初盘客队水位
                iiw = iil = il_text = liw = lil = ll_text = ''
                for idx in range(len(tds)):
                    val = tds[idx].get_text().strip().replace('\u00a0', '')
                    if idx == 3:
                        m = re.search(r'([\d\.]+)', val)
                        if m: iiw = m.group(1)
                    elif idx == 4:
                        il_text = val
                    elif idx == 5:
                        m = re.search(r'([\d\.]+)', val)
                        if m: iil = m.group(1)
                    elif idx == 9:
                        m = re.search(r'([\d\.]+)', val)
                        if m: liw = m.group(1)
                    elif idx == 10:
                        ll_text = val
                    elif idx == 11:
                        m = re.search(r'([\d\.]+)', val)
                        if m: lil = m.group(1)
                
                result['macau_line'] = il_text if il_text else ll_text
                result['macau_ih'] = iiw
                result['macau_il'] = iil
                break
        if result['macau_line']:
            break
    
    # 从页面提取队名 - 查找包含vs的链接
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        # 队名链接格式: /team/XXX/teamfixture/
        m = re.search(r'/team/(\d+)/teamfixture', href)
        if m:
            team_id = m.group(1)
            team_name = a.get_text().strip()
            if team_name and team_name not in ['首页', '列表', '亚盘', '欧赔', '让球', '比分']:
                if not result['home_name']:
                    result['home_id'] = team_id
                    result['home_name'] = team_name
                elif not result['away_name']:
                    result['away_id'] = team_id
                    result['away_name'] = team_name

except Exception as e:
    result['error'] = str(e)

# 如果亚盘页面没找到队名，尝试欧赔页面
if not result['home_id']:
    try:
        url = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(FID)
        r = sess.get(url, timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)/teamfixture', href)
            if m:
                team_id = m.group(1)
                team_name = a.get_text().strip()
                if team_name and len(team_name) > 1 and team_name not in ['首页', '列表', '亚盘', '欧赔', '让球', '比分']:
                    if not result['home_name']:
                        result['home_id'] = team_id
                        result['home_name'] = team_name
                    elif not result['away_name']:
                        result['away_id'] = team_id
                        result['away_name'] = team_name
    except:
        pass

# 如果还没找到，尝试让球页面
if not result['home_id']:
    try:
        url = 'https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(FID)
        r = sess.get(url, timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)/teamfixture', href)
            if m:
                team_id = m.group(1)
                team_name = a.get_text().strip()
                if team_name and len(team_name) > 1:
                    if not result['home_name']:
                        result['home_id'] = team_id
                        result['home_name'] = team_name
                    elif not result['away_name']:
                        result['away_id'] = team_id
                        result['away_name'] = team_name
    except:
        pass

# Write to file instead of stdout to avoid encoding issues
output_file = sys.argv[3] if len(sys.argv) > 3 else ''
if output_file:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    print(output_file)
else:
    # Fallback: stdout with ensure_ascii=True to avoid encoding issues
    print(json.dumps(result, ensure_ascii=True))
