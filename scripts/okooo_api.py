# -*- coding: utf-8 -*-
"""
澳客网(okooo.com)数据源API — 500.com EdgeOne 反爬封禁后的替代数据源
2026-09-01 实测: 接口需 http.client + 空Cookie头(urllib不带Cookie会被405拒绝)

接口:
  /soccer/match/{mid}/ah/ajax/    亚盘 30家(威廉希尔/皇冠/Bet365...)
  /soccer/match/{mid}/odds/ajax/  欧赔 30家(百家均/竞彩官方/威廉希尔/IW...)
  /soccer/match/{mid}/hodds/ajax/ 让球 45行(竞彩官方 -1/-2/-3...)
"""
import http.client, re, time, json, os

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# 全局 mid 映射缓存: {matchnum: mid}  e.g. {'周二002': '1332778'}
_MID_MAP = {}

# 盘口名 → 数值(与 4way _HANDICAP_ITEMS 同规则, 按名称长度降序)
_HANDICAP_ITEMS = sorted([
    ('平手', 0.0), ('平手/半球', -0.25), ('平半', -0.25),
    ('半球', -0.5), ('半球/一球', -0.75), ('半一', -0.75),
    ('一球', -1.0), ('一球/球半', -1.25), ('球半', -1.5),
    ('球半/两球', -1.75), ('两球', -2.0), ('两球/两球半', -2.25),
    ('两球半', -2.5), ('两球半/三球', -2.75), ('三球', -3.0),
    ('受平手/半球', 0.25), ('受平半', 0.25),
    ('受半球', 0.5), ('受半球/一球', 0.75), ('受半一', 0.75),
    ('受一球', 1.0), ('受一球/球半', 1.25),
    ('受球半', 1.5), ('受球半/两球', 1.75),
    ('受两球', 2.0), ('受两球/两球半', 2.25),
    ('受两球半', 2.5),
], key=lambda x: -len(x[0]))


def _req(host, path, headers, method='GET', body=None):
    conn = http.client.HTTPSConnection(host, timeout=15)
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    status = resp.status
    conn.close()
    return status, data


def _fetch_rows(mid, kind, retries=3):
    """抓取澳客比赛数据。kind: ah/odds/hodds。返回行列表[[cells...]]或None(带重试)
    2026-09-02: 阿里云WAF上线 — 直接GET ajax被拦(aliyun_waf挑战页)。放行链=
    同一连接先访问比赛主页 /soccer/match/{mid}/ 建立会话, 再GET ajax 才返回数据。
    必须复用同一个 http.client 连接(跨连接cookie不共享)。"""
    page_path = f'/soccer/match/{mid}/{kind}/'
    H_PAGE = {'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Language': 'zh-CN,zh;q=0.9'}
    H_AJAX = {'User-Agent': UA, 'Accept': 'text/html, */*; q=0.01', 'Accept-Language': 'zh-CN,zh;q=0.9',
              'Referer': 'https://www.okooo.com' + page_path,
              'X-Requested-With': 'XMLHttpRequest', 'Cookie': ''}
    for attempt in range(retries):
        try:
            conn = http.client.HTTPSConnection('www.okooo.com', timeout=15)
            try:
                # 1) 先访问比赛主页建会话(阿里云WAF放行前提)
                conn.request('GET', f'/soccer/match/{mid}/', headers=H_PAGE)
                r0 = conn.getresponse(); r0.read()
                time.sleep(0.35)
                # 2) kind 页面(ah/odds/hodds HTML, 同样过一遍WAF)
                conn.request('GET', page_path, headers=H_PAGE)
                r1 = conn.getresponse(); r1.read()
                time.sleep(0.35)
                # 3) ajax 数据
                conn.request('GET', page_path + 'ajax/', headers=H_AJAX)
                r2 = conn.getresponse()
                body = r2.read()
                s2 = r2.status
            finally:
                conn.close()
            if s2 != 200:
                time.sleep(2)
                continue
            text = body.decode('utf-8', errors='replace')
            if 'aliyun_waf' in text:
                time.sleep(2)
                continue
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', text, re.S)
            out = []
            for row in rows:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
                texts = [re.sub(r'<[^>]+>', '', c).replace('\xa0', ' ').replace('&nbsp;', ' ').strip() for c in tds]
                if texts and texts[0].isdigit():
                    out.append(texts)
            if out:
                return out
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return None


def load_mid_map(date_s=None):
    """从澳客竞彩页抓取当天全部场次的 matchnum→mid 映射(带缓存)"""
    global _MID_MAP
    if _MID_MAP:
        return _MID_MAP
    s, body = _req('www.okooo.com', '/jingcai/', {
        'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.8', 'Accept-Language': 'zh-CN,zh;q=0.9'})
    if s != 200:
        return {}
    text = body.decode('gbk', errors='replace')
    for m in re.finditer(r'data-mid="(\d+)"[^>]*data-morder="(\d+)"[^>]*data-ordercn="([^"]+)"', text):
        mid, morder, ordercn = m.groups()
        _MID_MAP[ordercn] = mid
    return _MID_MAP


def get_mid(matchnum):
    """matchnum(如'周二002') → 澳客mid; 未加载则尝试加载"""
    if not _MID_MAP:
        load_mid_map()
    return _MID_MAP.get(matchnum)


def hc_val(pan_text):
    """盘口名→数值, 如 '半球'→-0.5, '受平手/半球'→0.25"""
    txt = pan_text.replace('↑', '').replace('↓', '').replace('\xa0', '').strip()
    for name, val in _HANDICAP_ITEMS:
        if name in txt:
            return val
    try:
        return float(txt)
    except:
        return None


def find_row(rows, kw):
    """按公司名关键词找行(第2列)"""
    for r in rows:
        if len(r) > 1 and kw in r[1]:
            return r
    return None


def fetch_asian_hc(mid):
    """抓澳客亚盘威廉希尔: 返回 (即时盘数值, 初盘名, 即时盘名, 公司标签) 或 (None,'','','')"""
    if not mid:
        return None, '', '', ''
    rows = _fetch_rows(mid, 'ah')
    if not rows:
        return None, '', '', ''
    # 优先威廉希尔('威'), 无则第一行
    wh = find_row(rows, '威')
    row = wh if wh else rows[0]
    # row: [1, 公司, 初主水, 初盘, 初客水, 即主水, 即盘, 即客水]
    if len(row) < 8:
        return None, '', '', ''
    ip = row[3]
    lp = row[6]
    v = hc_val(lp)
    comp = '威廉希尔' if wh else row[1]
    return v, ip, lp, comp


def fetch_odds(mid):
    """抓澳客欧赔: 返回 (百家初终3值, 竞彩初终3值, IW初终3值)"""
    if not mid:
        return None, None, None
    rows = _fetch_rows(mid, 'odds')
    if not rows:
        return None, None, None
    # row: [1, 公司, 初胜, 初平, 初负, 终胜, 终平, 终负, ...]
    def _tri(row):
        try:
            return ([float(re.sub(r'[↑↓]', '', row[2])), float(re.sub(r'[↑↓]', '', row[3])), float(re.sub(r'[↑↓]', '', row[4]))],
                    [float(re.sub(r'[↑↓]', '', row[5])), float(re.sub(r'[↑↓]', '', row[6])), float(re.sub(r'[↑↓]', '', row[7]))])
        except:
            return None
    av = jc = iw = None
    av_row = find_row(rows, '均')    # 9***均 百家平均
    jc_row = find_row(rows, '竞')    # 竞**方 竞彩官方
    iw_row = find_row(rows, 'I')     # I*********n Interwetten
    if av_row: av = _tri(av_row)
    if jc_row: jc = _tri(jc_row)
    if iw_row: iw = _tri(iw_row)
    return av, jc, iw


def fetch_handicap(mid):
    """抓澳客让球: 返回 (竞彩官方行字典{让球,初3值,终3值}) 或 None"""
    if not mid:
        return None
    rows = _fetch_rows(mid, 'hodds')
    if not rows:
        return None
    jc_row = find_row(rows, '竞')
    if not jc_row:
        return None
    # row: [1, 竞**方, 让球数, 初胜, 初平, 初负, 终胜, 终平, 终负]
    if len(jc_row) < 9:
        return None
    try:
        return {
            'rq': jc_row[2],
            'init': [float(re.sub(r'[↑↓]', '', jc_row[3])), float(re.sub(r'[↑↓]', '', jc_row[4])), float(re.sub(r'[↑↓]', '', jc_row[5]))],
            'live': [float(re.sub(r'[↑↓]', '', jc_row[6])), float(re.sub(r'[↑↓]', '', jc_row[7])), float(re.sub(r'[↑↓]', '', jc_row[8]))],
        }
    except:
        return None


if __name__ == '__main__':
    # 自测
    mm = load_mid_map()
    print('mid映射:', mm)
    mid = mm.get('周二002', '')
    print('\n周二002 mid=', mid)
    v, ip, lp, comp = fetch_asian_hc(mid)
    print(f'威廉希尔亚盘: {comp} 初{ip} → 即{lp} ({v})')
    av, jc, iw = fetch_odds(mid)
    print(f'百家: {av}\n竞彩: {jc}\nIW: {iw}')
    hc = fetch_handicap(mid)
    print(f'让球: {hc}')
