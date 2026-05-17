# -*- coding: utf-8 -*-
"""
竞彩第26步：庄家盈亏占比分析
====================================

根据庄家盈亏数据（必发指数），计算：
- 胜/平/负 各方向的庄家盈亏状态
- 盈亏占比 = 该方向盈亏金额 / 总盈亏金额绝对值之和
- 带出历史同盈亏模式下的比分分布

用法：
    python step26_profit_ratio.py 2026-05-09
"""
import os, sys, json, re, io, requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, 'tasks')

# 500.com 投注分析接口
TOUZHU_URL = 'https://odds.500.com/fenxi/touzhu-{fid}.shtml'
# 比分统计接口
SCORE_URL = 'https://odds.500.com/fenxi/czgb-{fid}.shtml'


def load_matches_data(date_str):
    """读取matches_data.json获取比赛列表"""
    data_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    if not os.path.exists(data_file):
        return []
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_matches = []
    for group_name, group_data in data.get('groups', {}).items():
        if isinstance(group_data, dict) and 'matches' in group_data:
            for m in group_data['matches']:
                all_matches.append(m)
    return all_matches


def get_match_dir(date_str, match_num, match_home, match_away):
    """找到比赛对应的match目录"""
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    if not os.path.exists(data_dir):
        return None
    
    # 精确匹配：按meta.json中的matchnum（保留星期几前缀）
    for d in sorted(os.listdir(data_dir)):
        dp = os.path.join(data_dir, d)
        if not os.path.isdir(dp):
            continue
        mp = os.path.join(dp, 'meta.json')
        if os.path.exists(mp):
            try:
                meta = json.load(open(mp, 'r', encoding='utf-8'))
                mn = meta.get('matchnum', '')
                if mn == match_num:
                    return dp
            except:
                pass
    return None


def parse_zhuangjia_data(fid):
    """从500.com投注分析页面解析庄家盈亏数据"""
    url = TOUZHU_URL.format(fid=fid)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        result = {}
        # 匹配格式: 数字.数字 数字% 数字% 数字.数字 数字,数字 数字,数字
        data_pattern = r'([\d.]+)\s*(\d+\.?\d*)%\s*(?:-|–)\s*(\d+\.?\d*)%\s*([\d.]+)\s*([\d,]+)\s*(-?[\d,]+)'
        matches = re.findall(data_pattern, text)
        
        labels = ['主胜', '平局', '客胜']
        for i, m in enumerate(matches[:3]):
            label = labels[i] if i < 3 else f'unknown_{i}'
            result[label] = {
                'odds': m[0],
                'bet_pct': m[1],
                'fund_pct': m[2],
                'sp_odds': m[3],
                'volume': m[4],
                'profit_raw': m[5],
                'profit': int(m[5].replace(',', '').replace('-', '')) if m[5] else 0,
                'profit_dir': not m[5].startswith('-'),  # True=庄家赚钱(正数), False=庄家亏钱(负数)
            }
        return result
    except Exception as e:
        return {}


def parse_score_history(fid):
    """从500.com比分统计页面获取历史比分分布"""
    url = SCORE_URL.format(fid=fid)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        score_dist = {}
        # 提取比分表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 3:
                    try:
                        score = cols[0].get_text().strip()
                        count = cols[1].get_text().strip()
                        pct = cols[2].get_text().strip()
                        if score and count and '%' in pct:
                            score_dist[score] = {'count': count, 'pct': pct}
                    except:
                        pass
        return score_dist
    except:
        return {}


def run_profit_ratio_analysis(date_str):
    """运行盈亏占比分析"""
    matches = load_matches_data(date_str)
    if not matches:
        print('[ERROR] 未找到比赛数据')
        return
    
    print(f'找到 {len(matches)} 场比赛')
    
    results = []
    
    for match in matches:
        fid = match.get('fid', '')
        match_num = match.get('matchnum', '')
        home = match.get('home', '')
        away = match.get('away', '')
        
        if not fid:
            continue
        
        # 找到match目录
        match_dir = get_match_dir(date_str, match_num, home, away)
        if not match_dir:
            continue
        
        print(f'处理 {match_num} {home} vs {away} (fid={fid})...')
        
        # 解析庄家盈亏
        profit_data = parse_zhuangjia_data(fid)
        
        if not profit_data:
            print(f'  [WARN] 无庄家盈亏数据')
            continue
        
        # 计算盈亏占比
        total_abs = 0
        for label, info in profit_data.items():
            total_abs += info['profit']
        
        profit_ratio = {}
        if total_abs > 0:
            for label, info in profit_data.items():
                ratio = round(info['profit'] / total_abs, 4) if total_abs > 0 else 0
                profit_ratio[label] = {
                    'ratio': ratio,
                    'profit': info['profit'],
                    'bet_pct': info['bet_pct'],
                    'volume': info['volume'],
                    '庄家盈亏': info['profit_raw'],
                }
        
        # 获取历史比分分布
        score_dist = parse_score_history(fid)
        
        # 判断庄家盈亏状态
        result = {
            'match_num': match_num,
            'home': home,
            'away': away,
            'fid': fid,
            'profit_data': profit_data,
            'profit_ratio': profit_ratio,
            'score_dist': score_dist,
            'analysis': {}
        }
        
        # 综合分析
        # 胜平负 庄家盈亏方向
        zhuang_win = profit_data.get('主胜', {}).get('profit_dir', None)
        zhuang_draw = profit_data.get('平局', {}).get('profit_dir', None)
        zhuang_lose = profit_data.get('客胜', {}).get('profit_dir', None)
        
        analysis = {
            '庄家胜盈亏': '赢钱' if zhuang_win == True else ('亏钱' if zhuang_win == False else '未知'),
            '庄家平盈亏': '赢钱' if zhuang_draw == True else ('亏钱' if zhuang_draw == False else '未知'),
            '庄家负盈亏': '赢钱' if zhuang_lose == True else ('亏钱' if zhuang_lose == False else '未知'),
            '盈亏占比': {},
            '投注占比': {},
        }
        
        for label, info in profit_ratio.items():
            label_cn = label
            if label == '主胜':
                label_cn = '胜'
            elif label == '平局':
                label_cn = '平'
            elif label == '客胜':
                label_cn = '负'
            
            analysis['盈亏占比'][label_cn] = info['ratio']
            analysis['投注占比'][label_cn] = info['bet_pct']
        
        # 根据盈亏占比推断
        ratio_sum = sum(info['profit'] for info in profit_data.values())
        if ratio_sum > 0:
            # 找出庄家赢钱最多的方向（庄家最看好的方向）
            # 只考虑 profit_dir=True（庄家赢钱）的方向
            win_dirs = {k: v for k, v in profit_data.items() if v.get('profit_dir', False)}
            if win_dirs:
                # 庄家赢钱最多的方向 = 庄家最看好
                max_profit_label = max(win_dirs.items(), key=lambda x: x[1]['profit'])
                analysis['庄家最看好'] = max_profit_label[0].replace('主胜', '主胜').replace('平局', '平局').replace('客胜', '客胜')
            else:
                # 如果庄家所有方向都亏钱，选亏钱最少的方向
                lose_dirs = {k: v for k, v in profit_data.items() if v.get('profit_dir', True) == False}
                if lose_dirs:
                    min_lose_label = min(lose_dirs.items(), key=lambda x: x[1]['profit'])
                    analysis['庄家最看好'] = min_lose_label[0].replace('主胜', '主胜').replace('平局', '平局').replace('客胜', '客胜')
                else:
                    analysis['庄家最看好'] = '未知'
        
        result['analysis'] = analysis
        results.append(result)
        
        # 保存
        step26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
        with open(step26_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 显示分析结果
        print(f'  庄家盈亏: {analysis["庄家胜盈亏"]} / {analysis["庄家平盈亏"]} / {analysis["庄家负盈亏"]}')
        print(f'  盈亏占比: {json.dumps(analysis["盈亏占比"], ensure_ascii=False)}')
        print(f'  投注占比: {json.dumps(analysis["投注占比"], ensure_ascii=False)}')
        print(f'  已保存: {step26_file}')
    
    # 生成汇总
    summary_file = os.path.join(TASKS_DIR, date_str, 'data', 'step26_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date_str,
            'total': len(results),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f'\n[OK] 第26步完成: {len(results)} 场比赛')


if __name__ == '__main__':
    args = sys.argv[1:]
    date = args[0] if args else ''
    if not date:
        from datetime import datetime, timedelta
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f'📊 第26步：庄家盈亏占比分析 - {date}\n')
    run_profit_ratio_analysis(date)
    print('\n[OK] 第26步完成')
