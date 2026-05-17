# -*- coding: utf-8 -*-
"""
竞彩足球 - 第0步：获取当日竞彩比赛列表（多数据源 fallback）
独立运行，不与其他分析步骤合并
每天上午11点自动执行一次
也可手动触发：python step0_fetch_matches.py --date 2026-05-08
"""

import requests
import re
import os
import sys
import io

from _log_util import setup_logger
LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('step0', LOG_DIR)
import json
from datetime import datetime
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_sporttery(date_str):
    """源1：竞彩官网 sporttery.cn"""
    try:
        url = f'https://www.sporttery.cn/jc/jczq/jczqdz.shtml'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sporttery.cn/',
        }
        session = requests.Session()
        session.headers.update(headers)
        resp = session.get(url, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        matches = []
        # Try to find match table
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 4:
                matchnum = tds[0].get_text().strip()
                home = tds[1].get_text().strip()
                away = tds[2].get_text().strip()
                time = tds[3].get_text().strip() if len(tds) > 3 else ''
                league = tds[4].get_text().strip() if len(tds) > 4 else ''
                
                if matchnum and home and '00' in matchnum:
                    matches.append({
                        'matchnum': matchnum,
                        'home': home,
                        'away': away,
                        'time': time,
                        'league': league,
                        'rq': '',
                        'fid': '',
                    })
        
        if matches:
            return matches
        return None
    except Exception as e:
        log.info(f'  [sporttery] 获取失败: {e}')
        return None

def fetch_trade_500(date_str):
    """源2：trade.500.com"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        url = f'https://trade.500.com/jczq/?playid=269&g=2&date={date_str}'
        session = requests.Session()
        session.headers.update(headers)
        
        session.get('https://trade.500.com/', timeout=10)
        resp = session.get(url, timeout=15)
        html = resp.content.decode('gbk', errors='ignore')
        
        tr_blocks = re.findall(r'<tr[^>]*data-fixtureid="[^"]*"[^>]*>', html, re.DOTALL)
        
        matches = []
        for tr in tr_blocks:
            fid = re.search(r'data-fixtureid="(\d+)"', tr)
            matchnum = re.search(r'data-matchnum="([^"]*)"', tr)
            home = re.search(r'data-homesxname="([^"]*)"', tr)
            away = re.search(r'data-awaysxname="([^"]*)"', tr)
            time = re.search(r'data-matchtime="([^"]*)"', tr)
            rq = re.search(r'data-rangqiu="([^"]*)"', tr)
            league = re.search(r'data-simpleleague="([^"]*)"', tr)
            
            if fid and matchnum and home:
                matches.append({
                    'matchnum': matchnum.group(1),
                    'fid': fid.group(1),
                    'home': home.group(1),
                    'away': away.group(1) if away else '',
                    'time': time.group(1) if time else '',
                    'rq': rq.group(1) if rq else '',
                    'league': league.group(1) if league else '',
                })
        
        if matches:
            return matches
        return None
    except Exception as e:
        log.info(f'  [trade.500] 获取失败: {e}')
        return None

def fetch_odds_500(date_str):
    """源3：odds.500.com 赛程中心"""
    try:
        # 尝试从 odds.500.com/jczq/ 获取当日赛程
        url = f'https://odds.500.com/jczq/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        matches = []
        for tr in soup.find_all('tr', class_=lambda x: x and 'match' in x.lower()):
            tds = tr.find_all('td')
            if len(tds) >= 3:
                matchnum = tds[0].get_text().strip()
                home = tds[1].get_text().strip()
                away = tds[2].get_text().strip()
                if matchnum and home:
                    matches.append({
                        'matchnum': matchnum,
                        'home': home,
                        'away': away,
                        'time': '',
                        'league': '',
                        'rq': '',
                        'fid': '',
                    })
        
        if matches:
            return matches
        return None
    except Exception as e:
        log.info(f'  [odds.500] 获取失败: {e}')
        return None

def fetch_sunday_matches(date_str=None):
    """获取指定日期的竞彩比赛列表 - 多源 fallback"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    log.info(f'[FETCH] 尝试获取 {date_str} 竞彩比赛列表...')
    
    # 计算当天是周几
    target_date = datetime.strptime(date_str, '%Y-%m-%d')
    day_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
    expected_day = day_names[target_date.weekday()]
    
    # 源1: sporttery.cn
    log.info('  [源1] sporttery.cn...')
    matches = fetch_sporttery(date_str)
    if matches:
        log.info(f'  ✅ sporttery 获取成功: {len(matches)} 场')
        return matches
    
    # 源2: trade.500.com
    log.info('  [源2] trade.500.com...')
    matches = fetch_trade_500(date_str)
    if matches:
        # 过滤：只保留当天周几的比赛
        original_count = len(matches)
        matches = [m for m in matches if m['matchnum'][:2] == expected_day]
        log.info(f'  ✅ trade.500 获取成功: {len(matches)} 场 (过滤{original_count - len(matches)}场非当天)')
        return matches
    
    # 源3: odds.500.com
    log.info('  [源3] odds.500.com...')
    matches = fetch_odds_500(date_str)
    if matches:
        log.info(f'  ✅ odds.500 获取成功: {len(matches)} 场')
        return matches
    
    log.info(f'[WARN] 所有数据源均未获取到 {date_str} 的比赛数据')
    return None

def save_matches(matches, date_str, base_dir='jingcai/tasks'):
    """保存比赛数据到文件"""
    if not matches:
        return None
    
    task_dir = os.path.join(base_dir, date_str)
    os.makedirs(task_dir, exist_ok=True)
    
    # 按周几分组
    groups = {}
    for m in matches:
        day = m['matchnum'][:2]
        if day not in groups:
            groups[day] = []
        groups[day].append(m)
    
    result = {
        'date': date_str,
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'groups': {}
    }
    for day, day_matches in sorted(groups.items()):
        result['groups'][day] = {
            'count': len(day_matches),
            'matches': day_matches
        }
    
    # 保存JSON
    json_path = os.path.join(task_dir, 'matches_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 保存Markdown
    md_path = os.path.join(task_dir, 'sunday_matches.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f'# 竞彩足球 - {date_str} 比赛列表\n\n')
        f.write(f'📅 数据获取时间：{result["fetch_time"]}\n')
        f.write(f'📊 比赛日期：{date_str}\n')
        total = sum(g['count'] for g in result['groups'].values())
        f.write(f'📈 竞彩总场次：{total}场\n\n')
        f.write('---\n\n')
        
        for day, group in result['groups'].items():
            f.write(f'## {day}比赛\n\n')
            f.write('| 竞彩编号 | 主队 | 客队 | 联赛 | 时间 | 让球 | fid |\n')
            f.write('|---------|------|------|------|------|------|-----|\n')
            for m in group['matches']:
                f.write(f'| {m["matchnum"]} | {m["home"]} | {m["away"]} | {m.get("league","")} | {m["time"]} | {m.get("rq","")} | {m.get("fid","")} |\n')
            f.write('\n---\n\n')
    
    return json_path, md_path

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='获取当日竞彩比赛列表（多数据源）')
    parser.add_argument('--date', help='比赛日期（YYYY-MM-DD），默认今天')
    parser.add_argument('--output-dir', default='jingcai/tasks', help='输出目录')
    args = parser.parse_args()
    
    date_str = args.date or datetime.now().strftime('%Y-%m-%d')
    base_dir = args.output_dir
    
    log.info(f'[STEP] 第0步：获取竞彩比赛列表（多数据源 fallback）')
    log.info(f'[DATE] 比赛日期: {date_str}')
    
    matches = fetch_sunday_matches(date_str)
    
    if matches:
        # 增强：探测联赛映射
        try:
            from league_mapper import load_map, add_alias
            existing = load_map()
            new_leagues = set()
            for m in matches:
                jingcai_league = m.get('league', '')
                if jingcai_league and jingcai_league not in existing:
                    new_leagues.add(jingcai_league)
            
            if new_leagues:
                log.info(f'  [联赛探测] 发现 {len(new_leagues)} 个新联赛: {", ".join(new_leagues)}')
                for league in new_leagues:
                    add_alias(league, league)
                log.info(f'  [联赛探测] 映射表已更新')
        except ImportError:
            pass
        
        paths = save_matches(matches, date_str, base_dir)
        
        # 按周几分组显示
        groups = {}
        for m in matches:
            day = m['matchnum'][:2]
            if day not in groups:
                groups[day] = 0
            groups[day] += 1
        
        total = len(matches)
        log.info(f'[OK] 共 {total} 场比赛')
        for day, count in sorted(groups.items()):
            log.info(f'      {day}: {count}场')
        if paths:
            log.info(f'[FILE] JSON: {paths[0]}')
            log.info(f'[FILE] Markdown: {paths[1]}')
    else:
        log.info('[ERROR] 获取失败 - 所有数据源均无数据')
        sys.exit(1)
