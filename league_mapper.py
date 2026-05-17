# -*- coding: utf-8 -*-
"""
联赛映射管理模块
统一处理竞彩名 ↔ 源站名的映射关系
所有步骤脚本共享同一个 league_map.json 文件
"""
import os, json, re, requests, time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_FILE = os.path.join(SCRIPT_DIR, 'league_map.json')

# 内置基础映射（兜底，防止文件不存在）
BUILTIN_MAP = {
    '韩职': ['K1联赛', 'K联赛'],
    'K1联赛': ['韩职', 'K联赛'],
    'K联赛': ['韩职', 'K1联赛'],
    '日职': ['J1联赛', 'J1'],
    'J1联赛': ['日职', 'J1'],
    'J1': ['日职', 'J1联赛'],
    '日联': ['J2联赛', 'J2'],
    'J2联赛': ['日联'],
    'J2': ['日联', 'J2联赛'],
    '西甲': ['西甲'], '德甲': ['德甲'], '意甲': ['意甲'],
    '英超': ['英超'], '法甲': ['法甲'], '荷甲': ['荷甲'],
    '葡超': ['葡超'], '瑞超': ['瑞超', '瑞典超', '瑞典超级联赛'], '瑞典超': ['瑞超', '瑞典超', '瑞典超级联赛'], '瑞典超级联赛': ['瑞超', '瑞典超'], '挪超': ['挪超'],
    '丹超': ['丹超'], '比甲': ['比甲'], '土超': ['土超'],
    '俄超': ['俄超'], '巴甲': ['巴甲', '巴甲锦标赛'],
    '巴甲锦标赛': ['巴甲'], '巴乙': ['巴乙', '巴乙锦标赛'],
    '阿甲': ['阿甲', '阿根甲'],
    '美职足': ['美职足', '美国职业大联盟'],
    '沙特': ['沙特职业联赛', '沙特联'],
    '沙特职业联赛': ['沙特', '沙特联'],
    '沙特联': ['沙特', '沙特职业联赛'],
    '芬超': ['芬超', '芬兰'],
    '芬兰超级联赛': ['芬超'],
    '荷乙': ['荷乙'], '德乙': ['德乙'], '法乙': ['法乙'],
    '意乙': ['意乙'], '西乙': ['西乙'],
    '解放者杯': ['解放者杯', '南美解放者杯'],
    '南美解放者杯': ['解放者杯'],
    '欧冠': ['欧冠', '欧洲冠军联赛'],
    '欧联': ['欧联', '欧罗巴联赛', '欧罗巴'],
    '欧罗巴联赛': ['欧联', '欧罗巴'],
    '欧罗巴': ['欧联', '欧罗巴联赛'],
    '欧协联': ['欧协联', '欧洲协会联赛'],
    '欧洲协会联赛': ['欧协联'],
    '哥伦甲': ['哥伦甲', '哥伦比亚甲级联赛'],
    '哥伦比亚甲级联赛': ['哥伦甲'],
}

def load_map():
    """加载映射文件，如果不存在则返回内置映射"""
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 合并内置映射（文件优先）
            merged = dict(BUILTIN_MAP)
            merged.update(data)
            return merged
        except:
            pass
    return dict(BUILTIN_MAP)

# ============ 从 leagues_all.json 动态生成 BUILTIN_MAP（兜底） ============
def _build_builtin_map():
    """从 leagues_all.json 生成内置映射作为兜底"""
    all_file = os.path.join(SCRIPT_DIR, 'leagues_all.json')
    try:
        with open(all_file, 'r', encoding='utf-8') as f:
            all_leagues = json.load(f)
        result = {}
        for item in all_leagues:
            name = item['name']
            result[name] = [name]
        return result
    except:
        return {}

# 如果 league_map.json 不存在，从 leagues_all.json 生成兜底映射
if not os.path.exists(MAP_FILE):
    _extra = _build_builtin_map()
    if _extra:
        BUILTIN_MAP.update(_extra)
        print('  从 leagues_all.json 加载 {} 个联赛作为兜底'.format(len(_extra)))

def save_map(m):
    """保存映射到文件"""
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

def league_match(src_league, target_league):
    """
    联赛名模糊匹配
    src_league: 源站返回的联赛名（如 liansai.500.com 的 SIMPLEGBNAME）
    target_league: 竞彩使用的联赛名（如 trade.500.com 的 data-simpleleague）
    """
    if src_league == target_league:
        return True
    if not src_league or not target_league:
        return False
    
    m = load_map()
    
    # 精确别名匹配
    if target_league in m and src_league in m[target_league]:
        return True
    if src_league in m and target_league in m[src_league]:
        return True
    
    # 包含匹配（兜底）
    if len(target_league) >= 2 and target_league in src_league:
        return True
    if len(src_league) >= 2 and src_league in target_league:
        return True
    
    return False

def add_alias(key, alias):
    """添加联赛别名映射"""
    m = load_map()
    if key not in m:
        m[key] = []
    if alias and alias not in m[key]:
        m[key].append(alias)
    # 双向映射
    if alias not in m:
        m[alias] = []
    if key and key not in m[alias]:
        m[alias].append(key)
    save_map(m)

def discover_league_mapping(fid, sess=None):
    """
    通过 fid 从 liansai.500.com 探测联赛名映射
    返回 (竞彩联赛名, 源站联赛名)
    """
    if not fid:
        return None, None
    
    # 先通过 odds.500.com 获取 fixture 信息
    try:
        if sess is None:
            sess = requests.Session()
            sess.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
        
        url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        
        # 从页面提取联赛名（竞彩名）
        league_match = re.search(r'data-simpleleague="([^"]*)"', resp.text)
        jingcai_league = league_match.group(1) if league_match else ''
        
        if jingcai_league:
            # 记录映射（初始时源站名未知）
            add_alias(jingcai_league, jingcai_league)
            return jingcai_league, ''
    except:
        pass
    
    return None, None

def auto_discover_from_team(team_id, jingcai_league, sess=None):
    """
    从球队赛程页面自动发现源站联赛名
    当 filter3 返回0场时，调用此函数发现实际联赛名
    """
    if not team_id or not jingcai_league:
        return
    
    try:
        if sess is None:
            sess = requests.Session()
            sess.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
        
        url = f'https://liansai.500.com/team/{team_id}/teamfixture/'
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 收集所有 SIMPLEGBNAME
        src_leagues = set()
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                name = data.get('SIMPLEGBNAME', '')
                if name:
                    src_leagues.add(name)
            except:
                continue
        
        # 建立映射
        for src in src_leagues:
            add_alias(jingcai_league, src)
        
        return src_leagues
    except:
        return None

# 模块加载时确保映射文件存在
if not os.path.exists(MAP_FILE):
    save_map(BUILTIN_MAP)
