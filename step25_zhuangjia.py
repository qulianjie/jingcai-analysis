# -*- coding: utf-8 -*-
"""
竞彩第25步：庄家盈亏分析（必发指数）
====================================

从 500.com 投注分析页面获取：
- 投注占比（多/中/少）
- 庄家盈亏（多/中/少）

数据源：matches_data.json 中的 fid → https://odds.500.com/fenxi/touzhu-{fid}.shtml

用法：
    python step25_zhuangjia.py 2026-04-29
"""

import os, sys, re, json, io, requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, 'tasks')
TOUZHU_URL = 'https://odds.500.com/fenxi/touzhu-{fid}.shtml'


def load_matches_data(date_str):
    """读取matches_data.json获取fid"""
    # 优先找 tasks/{date}/matches_data.json，其次 tasks/{date}/data/matches_data.json
    data_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    if not os.path.exists(data_file):
        data_file = os.path.join(TASKS_DIR, date_str, 'data', 'matches_data.json')
    if not os.path.exists(data_file):
        return {}
    with open(data_file, 'rb') as f:
        raw = f.read().decode('utf-8')
    
    data = json.loads(raw)
    fid_map = {}  # {matchnum: fid}
    for group_key in data.get('groups', {}):
        group = data['groups'][group_key]
        for m in group.get('matches', []):
            num = m.get('matchnum', '')
            fid = m.get('fid', '')
            if num and fid:
                fid_map[num] = fid
    return fid_map


def parse_zhuangjia_data(fid):
    """从500.com投注分析页面解析庄家盈亏数据"""
    url = TOUZHU_URL.format(fid=fid)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gb2312'
        text = resp.text
        
        # 提取投注分布和庄家盈亏
        # 页面文本格式: 水户蜀葵3.5625.9%-25.2%4.1230,460-32,101--3-4平局3.1429.4%-5.0%3.4546,014754,037--8382町田泽维亚2.0744.6%-69.7%2.16636,311-461,647-56-51
        # 提取: 赔率 投注占比 成交量 庄家盈亏
        
        result = {}
        
        # 用BeautifulSoup辅助解析
        soup = BeautifulSoup(text, 'html.parser')
        full_text = soup.get_text()
        
        # 从文本中提取投注分布三行
        # 格式: 主胜/客队 赔率 投注占比 资金占比 赔率 成交量 庄家盈亏
        patterns = [
            ('主胜', r'(?:主胜|[\u4e00-\u9fff]{2,4})\s*([\d.]+)\s*(\d+\.?\d*)%\s*(?:-|–)\s*(\d+\.?\d*)%\s*([\d.]+)\s*([\d,]+)\s*(-?[\d,]+)'),
            ('平局', r'平\s*([\d.]+)\s*(\d+\.?\d*)%\s*(?:-|–)\s*(\d+\.?\d*)%\s*([\d.]+)\s*([\d,]+)\s*(-?[\d,]+)'),
            ('客胜', r'(?:客胜|[\u4e00-\u9fff]{2,4})\s*([\d.]+)\s*(\d+\.?\d*)%\s*(?:-|–)\s*(\d+\.?\d*)%\s*([\d.]+)\s*([\d,]+)\s*(-?[\d,]+)'),
        ]
        
        # 更简单的方法：直接提取所有关键数字块
        # 格式示例: 3.56 25.9% 25.2% 4.1 230,460 -32,101
        # 三行分别对应主胜/平局/客胜
        
        # 从完整文本中提取包含赔率和百分比的数据块
        # 查找模式: 数字.数字 数字% 数字% 数字.数字 数字,数字 负数
        data_pattern = r'([\d.]+)\s*(\d+\.?\d*)%\s*(?:-|–)\s*(\d+\.?\d*)%\s*([\d.]+)\s*([\d,]+)\s*(-?[\d,]+)'
        matches = re.findall(data_pattern, full_text)
        
        labels = ['主胜', '平局', '客胜']
        for i, m in enumerate(matches[:3]):
            label = labels[i] if i < 3 else f'unknown_{i}'
            result[label] = {
                'odds': m[0],
                'bet_pct': m[1],
                'fund_pct': m[2],
                'sp_odds': m[3],
                'volume': m[4],
                'profit': m[5].replace('-', ''),
            }
        
        # 提取庄家盈亏指数
        # 格式: --3-4, --8382, -56-51
        profit_pattern = r'(?:-|–)\s*(\d+)\s*(?:-|–)\s*(\d+)'
        profit_matches = re.findall(profit_pattern, full_text)
        
        return result
    except Exception as e:
        print(f'  [WARN] 解析fid={fid}失败: {e}')
        return {}


def classify_value(value, thresholds):
    """分类：多/中/少"""
    try:
        v = float(str(value).replace(',', ''))
        if v >= thresholds[1]:
            return '多'
        elif v >= thresholds[0]:
            return '中'
        else:
            return '少'
    except:
        return '少'


def run_analysis(date_str):
    """运行第25步分析"""
    date_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(date_dir):
        print(f'[ERROR] 任务目录不存在: {date_dir}')
        return
    
    # 读取fid映射
    fid_map = load_matches_data(date_str)
    if not fid_map:
        print('[ERROR] 未找到matches_data.json')
        return
    
    print(f'  找到 {len(fid_map)} 场比赛的fid')
    
    # 阈值
    volume_thresholds = [10000, 100000]  # 成交量：少<1万<中<10万<多
    profit_thresholds = [50000, 300000]  # 庄家盈亏：少<5万<中<30万<多
    bet_pct_thresholds = [20, 40]  # 投注占比：少<20%<中<40%<多
    
    data_dir = os.path.join(date_dir, 'data')
    
    for match_num in sorted(fid_map.keys()):
        fid = fid_map[match_num]
        
        print(f'  处理 {match_num} (fid={fid})...')
        
        # 解析数据
        raw_data = parse_zhuangjia_data(fid)
        
        if not raw_data:
            print(f'    [WARN] 未解析到数据')
            continue
        
        # 分类
        labels = {}
        for label, info in raw_data.items():
            labels[label] = {
                'bet_pct': classify_value(info.get('bet_pct', 0), bet_pct_thresholds),
                'volume': classify_value(info.get('volume', 0), volume_thresholds),
                'profit': classify_value(info.get('profit', 0), profit_thresholds),
                'raw': info
            }
        
        # 保存
        result = {
            'match_num': match_num,
            'fid': fid,
            'url': TOUZHU_URL.format(fid=fid),
            'data': raw_data,
            'labels': {k: {kk: vv for kk, vv in v.items() if kk != 'raw'} for k, v in labels.items()}
        }
        
        # 找到match目录（按match_num精确匹配）
        match_dir = None
        if os.path.exists(data_dir):
            for d in sorted(os.listdir(data_dir)):
                dp = os.path.join(data_dir, d)
                if not os.path.isdir(dp):
                    continue
                # 精确匹配：先检查meta.json
                mp = os.path.join(dp, 'meta.json')
                if os.path.exists(mp):
                    try:
                        mm = json.load(open(mp, 'r', encoding='utf-8'))
                        mn = mm.get('matchnum', '')
                        if mn == match_num:
                            match_dir = dp
                            break
                    except:
                        pass
        
        if not match_dir:
            match_dir = data_dir
            print(f'    [WARN] 未找到{match_num}目录，数据写入data/根目录')
        
        step25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
        with open(step25_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f'    已保存: {step25_file}')
        
        # 显示结果
        for label, info in labels.items():
            raw = info['raw']
            print(f'    {label}: 赔率={raw.get("odds","?")} 投注占比={info["bet_pct"]}({raw.get("bet_pct","")}%) 成交量={info["volume"]} 庄家盈亏={info["profit"]}')


if __name__ == '__main__':
    args = sys.argv[1:]
    date = args[0] if args else ''
    if not date:
        from datetime import datetime, timedelta
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f'📊 第25步：庄家盈亏分析 - {date}\n')
    run_analysis(date)
    print('\n[OK] 第25步完成')
