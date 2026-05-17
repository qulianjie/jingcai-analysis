# -*- coding: utf-8 -*-
"""
竞彩足球 - 第0步：获取当日竞彩比赛列表
独立运行，不与其他分析步骤合并
每天上午11点自动执行一次
也可手动触发：命令助理"跑第0步"或"更新今日竞彩列表"
"""

import requests
import re
import os
import sys
import io
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_sunday_matches(date_str=None):
    """获取指定日期的竞彩比赛列表"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
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
    
    try:
        session.get('https://trade.500.com/', timeout=10)
        resp = session.get(url, timeout=15)
        html = resp.content.decode('gbk', errors='ignore')
    except Exception as e:
        print(f'[ERROR] 获取数据失败: {e}')
        return None
    
    # 提取所有<tr>比赛行
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
                'matchnum': matchnum.group(1),  # 如"周日001"
                'fid': fid.group(1),
                'home': home.group(1),
                'away': away.group(1) if away else '',
                'time': time.group(1) if time else '',
                'rq': rq.group(1) if rq else '',
                'league': league.group(1) if league else '',
            })
    
    if not matches:
        print(f'[WARN] 未找到 {date_str} 的比赛数据')
        return None
    
    # 按周几分组
    groups = {}
    for m in matches:
        # Extract day prefix: 周一/周二/周三/周四/周五/周六/周日
        day = m['matchnum'][:2]  # e.g. '周一'
        if day not in groups:
            groups[day] = []
        groups[day].append(m)
    
    # Filter: only keep matches for the requested date's day-of-week
    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
    target_day = weekday_map[datetime.strptime(date_str, '%Y-%m-%d').weekday()]
    filtered_groups = {target_day: groups.get(target_day, [])} if target_day in groups else {}
    
    result = {
        'date': date_str,
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'groups': {}
    }
    for day, day_matches in sorted(filtered_groups.items()):
        result['groups'][day] = {
            'count': len(day_matches),
            'matches': day_matches
        }
    
    return result

def save_matches(result, base_dir='jingcai/tasks'):
    """保存比赛数据到文件"""
    if not result:
        return
    
    date_str = result['date']
    task_dir = os.path.join(base_dir, date_str)
    os.makedirs(task_dir, exist_ok=True)
    
    # 保存JSON数据
    json_path = os.path.join(task_dir, 'matches_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 保存Markdown表格
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
                f.write(f'| {m["matchnum"]} | {m["home"]} | {m["away"]} | {m["league"]} | {m["time"]} | {m["rq"]} | {m["fid"]} |\n')
            f.write('\n---\n\n')
        f.write('## 数据来源\n')
        f.write(f'- URL: https://trade.500.com/jczq/?playid=269&g=2&date={date_str}\n')
        f.write('- 获取方式: Python requests + Session + 完整浏览器请求头 + GBK解码\n')
        f.write('- 识别方法: 用 `<tr>` 标签的 `data-matchnum` 属性区分周六/周日\n')
    
    return json_path, md_path

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='获取当日竞彩比赛列表')
    parser.add_argument('--date', help='比赛日期（YYYY-MM-DD），默认今天')
    parser.add_argument('--output-dir', default='jingcai/tasks', help='输出目录')
    args = parser.parse_args()
    
    date_str = args.date
    base_dir = args.output_dir
    
    print(f'[STEP] 第0步：获取竞彩比赛列表')
    print(f'[DATE] 比赛日期: {date_str or "今天"}')
    
    result = fetch_sunday_matches(date_str)
    
    if result:
        paths = save_matches(result, base_dir)
        total = sum(g['count'] for g in result['groups'].values())
        print(f'[OK] Total {total} matches')
        for day, group in result['groups'].items():
            print(f'      {day}: {group["count"]}场')
        print(f'[FILE] JSON: {paths[0]}')
        print(f'[FILE] Markdown: {paths[1]}')
    else:
        print('[ERROR] 获取失败')
        sys.exit(1)
