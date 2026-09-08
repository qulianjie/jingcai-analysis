# -*- coding: utf-8 -*-
"""
竞彩第25步：庄家盈亏 + 投注占比分析
=====================================
（合并原 step25 + step26，消除重复请求）

从 500.com 投注分析页面 touzhu-{fid}.shtml 提取：
- 投注占比（多/中/少）
- 庄家盈亏（多/中/少）
- 盈亏占比计算
- 历史比分分布（czgb-{fid}.shtml）

数据源：matches_data.json 中的 fid

用法：
    python step25_zhuangjia.py 2026-04-29       # 单日
    python step25_zhuangjia.py 2026-04-29 --all   # 所有比赛（含step26分析）
"""

import os, sys, re, json, io, requests
from _http_cache import CachedSession
from _log_util import setup_logger
from _util import TOUZHU_URL, SCORE_URL, load_matches_data, load_matches_list, safe_json_dump
from bs4 import BeautifulSoup

# 全局缓存 Session
_cache_session = None
def _get_sess():
    global _cache_session
    if _cache_session is None:
        _cache_session = CachedSession(headers=HEADERS)
    return _cache_session

LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('step25', LOG_DIR)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 优先使用versions/base/tasks/（与run_pipeline.py一致）
BASE_TASKS = os.path.join(BASE_DIR, 'versions', 'base', 'tasks')
if False:
    TASKS_DIR = BASE_TASKS
else:
    TASKS_DIR = os.path.join(BASE_DIR, 'tasks')

# 阈值
VOLUME_THRESHOLDS = [10000, 100000]     # 成交量：少<1万<中<10万<多
PROFIT_THRESHOLDS = [50000, 300000]     # 庄家盈亏：少<5万<中<30万<多
BET_PCT_THRESHOLDS = [20, 40]           # 投注占比：少<20%<中<40%<多

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


# ============ 网络提取 ============

def parse_zhuangjia_data(fid):
    """从 500.com 投注分析页面解析庄家盈亏和投注占比数据
    用 BeautifulSoup 表格解析替代正则，避免单元格分行导致的错位bug
    """
    url = TOUZHU_URL.format(fid=fid)
    
    try:
        resp = _get_sess().get(url, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        result = {}
        # 找包含百家欧赔+必发数据的表格
        tables = soup.find_all('table')
        data_table = None
        for tbl in tables:
            txt = tbl.get_text()
            if '庄家盈亏' in txt and '必发' in txt and '百家欧指' in txt:
                data_table = tbl
                break
        
        if data_table:
            rows = data_table.find_all('tr')
            # 数据行: row index 2=主胜, 3=平局, 4=客胜（跳过表头前2行）
            data_rows = []
            for r in rows[2:]:  # 从第3行开始
                cells = r.find_all(['td', 'th'])
                vals = [c.get_text(strip=True) for c in cells]
                if len(vals) >= 8:
                    # vals[0]=队名, [1]=赔率, [2]=投注占比%, [3]-[4]=资金占比
                    # [5]=SP赔率, [6]=成交量, [7]=庄家盈亏
                    data_rows.append(vals)
                    if len(data_rows) >= 3:
                        break
            
            label_order = ['主胜', '平局', '客胜']
            for idx, row in enumerate(data_rows[:3]):
                label = label_order[idx]
                
                odds = row[1] if len(row) > 1 else ''
                bet_pct = row[2].replace('%', '') if len(row) > 2 and '%' in row[2] else ''
                # 资金占比在 col 4（下标3是分隔符'-'）
                fund_pct = ''
                if len(row) > 4:
                    fp = row[4]
                    if '%' in fp:
                        fund_pct = fp.replace('%', '')
                    elif fp == '-':
                        fund_pct = '--'
                
                sp_odds = row[5] if len(row) > 5 else ''
                volume = row[6] if len(row) > 6 and row[6] != '-' else ''
                profit_raw = row[7] if len(row) > 7 and row[7] != '-' else '0'
                
                result[label] = {
                    'odds': odds,
                    'bet_pct': bet_pct,
                    'fund_pct': fund_pct,
                    'sp_odds': sp_odds,
                    'volume': volume,
                    'profit_raw': profit_raw,
                    'profit': int(profit_raw.replace(',', '')) if profit_raw else 0,
                    'profit_dir': not profit_raw.startswith('-') if profit_raw and profit_raw != '0' else None,
                }
        
        # 表格解析漏掉的场次，用正则回退
        labels = ['主胜', '平局', '客胜']
        filled = [l for l in labels if l in result]
        missing = [l for l in labels if l not in result]
        
        if missing:
            text = soup.get_text()
            fallback = re.findall(r'庄家盈亏\s+(-?[\d,]+)\s+(-?[\d,]+)\s+(-?[\d,]+)', text)
            if fallback:
                profits = fallback[0]
                for i, label in enumerate(labels):
                    if label in result:
                        continue
                    raw = profits[i] if i < len(profits) else ''
                    result[label] = {
                        'odds': '', 'bet_pct': '', 'fund_pct': '',
                        'sp_odds': '', 'volume': '',
                        'profit_raw': raw,
                        'profit': int(raw.replace(',', '')) if raw and raw != '--' else 0,
                        'profit_dir': not raw.startswith('-') if raw and raw not in ('--', '0') else None,
                    }
        
        return result
    except Exception as e:
        log.warning(f'[step25] touzhu-{fid} 解析失败: {e}')
        import traceback
        log.warning(traceback.format_exc())
        return {}


def parse_score_history(fid):
    """从 500.com 比分统计页面获取历史比分分布"""
    url = SCORE_URL.format(fid=fid)
    
    try:
        resp = _get_sess().get(url, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        score_dist = {}
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 3:
                    try:
                        score = cols[0].get_text().strip()
                        count = cols[1].get_text().strip()
                        pct = cols[2].get_text().strip()
                        if score and count and '%' in pct:
                            score_dist[score] = {'count': count, 'pct': pct}
                    except Exception as e:
                        raise RuntimeError(f'[step25] czgb表解析失败: {e}')
        return score_dist
    except Exception as e:
        raise RuntimeError(f'[step25] parse_score_history 失败: {e}')


# ============ 分类分析 ============

def classify_value(value, thresholds):
    """分类：多/中/少"""
    try:
        s = str(value).replace(',', '').strip()
        if not s:
            return '少'  # 空值（源站未提供成交量）归最少档，不崩整场
        v = float(s)
        if v >= thresholds[1]:
            return '多'
        elif v >= thresholds[0]:
            return '中'
        else:
            return '少'
    except Exception as e:
        raise RuntimeError(f'[step25] classify_value 解析失败: {e}')


def analyze_profit_ratio(profit_data):
    """计算盈亏占比和庄家意向"""
    if not profit_data:
        return {}
    
    total_abs = sum(abs(info.get('profit', 0)) for info in profit_data.values())
    
    profit_ratio = {}
    if total_abs > 0:
        for label, info in profit_data.items():
            ratio = round(info['profit'] / total_abs, 4) if total_abs > 0 else 0
            profit_ratio[label] = {
                'ratio': ratio,
                'profit': info['profit'],
                'bet_pct': info.get('bet_pct', '0'),
                'volume': info.get('volume', '0'),
                'profit_raw': info.get('profit_raw', ''),
            }
    
    # 庄家方向分析
    zhuang_win = profit_data.get('主胜', {}).get('profit_dir', None)
    zhuang_draw = profit_data.get('平局', {}).get('profit_dir', None)
    zhuang_lose = profit_data.get('客胜', {}).get('profit_dir', None)
    
    analysis = {
        '庄家胜盈亏': '赢钱' if zhuang_win is True else ('亏钱' if zhuang_win is False else '0'),
        '庄家平盈亏': '赢钱' if zhuang_draw is True else ('亏钱' if zhuang_draw is False else '0'),
        '庄家负盈亏': '赢钱' if zhuang_lose is True else ('亏钱' if zhuang_lose is False else '0'),
        '盈亏占比': {},
        '投注占比': {},
    }
    
    for label, info in profit_ratio.items():
        lc = '胜' if label == '主胜' else ('平' if label == '平局' else '负')
        analysis['盈亏占比'][lc] = info['ratio']
        analysis['投注占比'][lc] = info.get('bet_pct', '0').replace('%', '')
    
    # 庄家最看好方向
    win_dirs = {k: v for k, v in profit_data.items() if v.get('profit_dir', False)}
    if win_dirs:
        max_label = max(win_dirs.items(), key=lambda x: x[1]['profit'])
        analysis['庄家最看好'] = max_label[0]
    else:
        lose_dirs = {k: v for k, v in profit_data.items() if not v.get('profit_dir', True)}
        if lose_dirs:
            min_label = min(lose_dirs.items(), key=lambda x: x[1]['profit'])
            analysis['庄家最看好'] = min_label[0]
        else:
            analysis['庄家最看好'] = '未知'
    
    return {
        'profit_ratio': profit_ratio,
        'analysis': analysis,
    }


# ============ 匹配目录 ============

def find_match_dir(date_str, match_num):
    """按 matchnum 找到对应的 match 目录"""
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    if not os.path.exists(data_dir):
        return None
    
    for d in sorted(os.listdir(data_dir)):
        dp = os.path.join(data_dir, d)
        if not os.path.isdir(dp):
            continue
        mp = os.path.join(dp, 'meta.json')
        if os.path.exists(mp):
            try:
                meta = json.load(open(mp, 'r', encoding='utf-8'))
                if meta.get('matchnum', '') == match_num:
                    return dp
            except Exception as e: raise RuntimeError(f'[{fname}] 操作失败: {e}')
    return None


# ============ 主流程 ============

def run_analysis(date_str, run_full=False):
    """运行第25步 + 第26步分析
    
    Args:
        date_str: 日期 YYYY-MM-DD
        run_full: True=同时跑 step26 的比分分析，False=只跑基础投注/庄家
    """
    date_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(date_dir):
        log.info(f'[ERROR] 任务目录不存在: {date_dir}')
        return
    
    # 读取 fid 映射
    fid_map = load_matches_data(date_str, TASKS_DIR)
    if not fid_map:
        log.info('[ERROR] 未找到 matches_data.json')
        return
    
    # 扁平化：支持两种格式
    # 格式A: {'周三001': 1363570, ...}  (旧格式，match_num->fid)
    # 格式B: {date, fetch_time, groups: {group: {matches: [...]}}} (step0分组格式)
    flat_fids = {}
    for k, v in fid_map.items():
        if k in ('date', 'fetch_time'):
            continue
        if isinstance(v, dict) and 'matches' in v:
            for m in v['matches']:
                flat_fids[m['matchnum']] = m['fid']
        elif isinstance(v, dict):
            for gk, gv in v.items():
                if isinstance(gv, dict) and 'matches' in gv:
                    for m in gv['matches']:
                        flat_fids[m['matchnum']] = m['fid']
        else:
            flat_fids[k] = v
    
    log.info(f'  找到 {len(flat_fids)} 场比赛的 fid')
    
    count25 = 0
    count26 = 0
    
    for match_num in sorted(flat_fids.keys()):
        fid = flat_fids[match_num]
        log.info(f'  处理 {match_num} (fid={fid})...')
        
        # 找到 match 目录
        match_dir = find_match_dir(date_str, match_num)
        if not match_dir:
            match_dir = os.path.join(TASKS_DIR, date_str, 'data')
        
        # ======== 第25步：基础投注+庄家盈亏 ========
        raw_data = parse_zhuangjia_data(fid)
        
        if not raw_data:
            log.info(f'    [WARN] 无投注/庄家数据')
            continue
        
        # 分类
        labels = {}
        for label, info in raw_data.items():
            labels[label] = {
                'bet_pct': classify_value(info.get('bet_pct', 0), BET_PCT_THRESHOLDS),
                'volume': classify_value(info.get('volume', 0), VOLUME_THRESHOLDS),
                'profit': classify_value(info.get('profit', 0), PROFIT_THRESHOLDS),
                'raw': info,
            }
        
        result25 = {
            'match_num': match_num,
            'fid': fid,
            'url': TOUZHU_URL.format(fid=fid),
            'data': raw_data,
            'labels': {k: {kk: vv for kk, vv in v.items() if kk != 'raw'} for k, v in labels.items()},
        }
        
        step25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
        safe_json_dump(result25, step25_file, indent=2)
        log.info(f'    第25步已保存: {step25_file}')
        count25 += 1
        
        for label, info in labels.items():
            raw = info['raw']
            log.info(f'    {label}: 赔率={raw.get("odds","?")} 投注占比={info["bet_pct"]}({raw.get("bet_pct","")}%) 成交量={info["volume"]} 庄家盈亏={info["profit"]}')
        
        # ======== 第26步：盈亏占比 + 比分分布（可选项） ========
        if run_full:
            profit_analysis = analyze_profit_ratio(raw_data)
            score_dist = parse_score_history(fid)
            
            result26 = {
                'match_num': match_num,
                'fid': fid,
                'profit_data': raw_data,
                'profit_ratio': profit_analysis['profit_ratio'],
                'score_dist': score_dist,
                'analysis': profit_analysis['analysis'],
            }
            
            step26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
            safe_json_dump(result26, step26_file, indent=2)
            log.info(f'    第26步已保存: {step26_file}')
            count26 += 1
            
            a = profit_analysis['analysis']
            log.info(f'    庄家盈亏: {a["庄家胜盈亏"]} / {a["庄家平盈亏"]} / {a["庄家负盈亏"]}')
            log.info(f'    庄家最看好: {a["庄家最看好"]}')
    
    log.info(f'\n[OK] 第25步完成: {count25} 场比赛')
    if run_full:
        log.info(f'[OK] 第26步同步完成: {count26} 场比赛')


def run_single_match(match_dir, run_full=True):
    """为单场比赛运行 step25 + step26
    
    从 match_dir/meta.json 读取 FID，单独处理一场。
    支持在 run_pipeline 的 per-match 步骤中直接调用。
    """
    meta_path = os.path.join(match_dir, 'meta.json')
    if not os.path.exists(meta_path):
        log.info(f'[ERROR] meta.json 不存在: {meta_path}')
        return False
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.loads(f.read())
    except Exception as e:
        log.info(f'[ERROR] 读取 meta.json 失败: {e}')
        return False
    
    fid = meta.get('fid', '')
    match_num = meta.get('matchnum', '')
    if not fid:
        log.info(f'[ERROR] meta.json 中无 fid')
        return False
    
    log.info(f'  [单场] {match_num} (fid={fid})...')
    
    # step25: 庄家盈亏
    raw_data = parse_zhuangjia_data(fid)
    if not raw_data:
        log.info(f'    [WARN] 无投注/庄家数据')
        return False
    
    labels = {}
    for label, info in raw_data.items():
        labels[label] = {
            'bet_pct': classify_value(info.get('bet_pct', 0), BET_PCT_THRESHOLDS),
            'volume': classify_value(info.get('volume', 0), VOLUME_THRESHOLDS),
            'profit': classify_value(info.get('profit', 0), PROFIT_THRESHOLDS),
            'raw': info,
        }
    
    result25 = {
        'match_num': match_num,
        'fid': fid,
        'url': TOUZHU_URL.format(fid=fid),
        'data': raw_data,
        'labels': {k: {kk: vv for kk, vv in v.items() if kk != 'raw'} for k, v in labels.items()},
    }
    
    step25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
    safe_json_dump(result25, step25_file, indent=2)
    log.info(f'    第25步已保存: {step25_file}')
    
    for label, info in labels.items():
        raw = info['raw']
        log.info(f'    {label}: 赔率={raw.get("odds","?")} 投注占比={info["bet_pct"]}({raw.get("bet_pct","")}%) 成交量={info["volume"]} 庄家盈亏={info["profit"]}')
    
    # step26: 盈亏占比
    if run_full:
        profit_analysis = analyze_profit_ratio(raw_data)
        result26 = {
            'match_num': match_num,
            'fid': fid,
            'profit_data': raw_data,
            'profit_ratio': profit_analysis['profit_ratio'],
            'analysis': profit_analysis['analysis'],
        }
        step26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
        safe_json_dump(result26, step26_file, indent=2)
        log.info(f'    第26步已保存: {step26_file}')
        
        a = profit_analysis['analysis']
        log.info(f'    庄家盈亏: {a["庄家胜盈亏"]} / {a["庄家平盈亏"]} / {a["庄家负盈亏"]}')
        log.info(f'    庄家最看好: {a["庄家最看好"]}')
    
    return True


if __name__ == '__main__':
    args = sys.argv[1:]
    date = ''
    run_full = False
    
    # 支持 --match-dir <path> 模式（run_pipeline per-match 调用）
    for i, a in enumerate(args):
        if a == '--match-dir' and i + 1 < len(args):
            match_dir_arg = args[i + 1]
            if os.path.isdir(match_dir_arg):
                run_single_match(match_dir_arg, run_full=True)
                log.info('[DONE]')
                sys.exit(0)
            else:
                log.info(f'[ERROR] 无效的 match_dir: {match_dir_arg}')
                sys.exit(1)
    
    for a in args:
        if a == '--all' or a == '--full':
            run_full = True
        elif a.startswith('2') and '-' in a:
            date = a
    
    if not date:
        from datetime import datetime, timedelta
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    log.info(f'📊 第25步：庄家盈亏+投注占比分析 - {date}')
    if run_full:
        log.info(f'   [全量模式] 含盈亏占比+比分分布')
    log.info('')
    
    run_analysis(date, run_full=run_full)
    
    log.info('')
    if not run_full:
        log.info(f'[HINT] 如需完整盈亏占比分析，请加 --all 参数')
    log.info('[DONE]')
