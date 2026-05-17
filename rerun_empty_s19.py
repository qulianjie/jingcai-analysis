# -*- coding: utf-8 -*-
"""
重跑step19空数据的比赛，并分析失败原因
step19 阈值: >1738 bytes
"""
import os, sys, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, 'tasks')

S19_THRESHOLD = 1738

def find_empty_s19():
    """找出所有step19空数据的比赛"""
    dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', 
             '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']
    
    empty_list = []
    for date in dates:
        data_dir = os.path.join(TASKS_DIR, date, 'data')
        if not os.path.isdir(data_dir):
            continue
        
        matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match')])
        for m in matches:
            base = os.path.join(data_dir, m)
            step19 = os.path.join(base, 'group06_baijia', 'step19_baijia_compare.txt')
            
            if os.path.exists(step19):
                size = os.path.getsize(step19)
                if size <= S19_THRESHOLD:
                    meta_path = os.path.join(base, 'meta.json')
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        empty_list.append({
                            'date': date,
                            'name': m,
                            'dir': base,
                            'league': meta.get('league', ''),
                            'home': meta.get('home', ''),
                            'away': meta.get('away', ''),
                            'fid': meta.get('fid', ''),
                            'home_id': meta.get('home_id', ''),
                            'away_id': meta.get('away_id', ''),
                            'macau_line': meta.get('macau_line', ''),
                            'old_size': size
                        })
    
    return empty_list

def rerun_one(match_info):
    """重跑单场比赛的step19"""
    date = match_info['date']
    name = match_info['name']
    match_dir = match_info['dir']
    league = match_info['league']
    
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, 'step8_1923_extractor.py'), match_dir],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        
        step19 = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')
        if os.path.exists(step19):
            new_size = os.path.getsize(step19)
        else:
            new_size = 0
        
        success = new_size > S19_THRESHOLD
        
        return {
            'date': date,
            'name': name,
            'league': league,
            'success': success,
            'old_size': match_info['old_size'],
            'new_size': new_size,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'date': date,
            'name': name,
            'league': league,
            'success': False,
            'old_size': match_info['old_size'],
            'new_size': 0,
            'error': 'timeout'
        }
    except Exception as e:
        return {
            'date': date,
            'name': name,
            'league': league,
            'success': False,
            'old_size': match_info['old_size'],
            'new_size': 0,
            'error': str(e)
        }

def main():
    print('正在查找step19空数据的比赛...')
    empty_matches = find_empty_s19()
    print('找到 %d 场空数据比赛\n' % len(empty_matches))
    
    # 按联赛分组统计
    league_stats = {}
    for m in empty_matches:
        league = m['league']
        if league not in league_stats:
            league_stats[league] = 0
        league_stats[league] += 1
    
    print('按联赛分布:')
    for league, count in sorted(league_stats.items(), key=lambda x: -x[1]):
        print('  %s: %d场' % (league, count))
    print('')
    
    print('开始重跑...')
    success = 0
    failed = []
    
    # 并发处理（3个并发）
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(rerun_one, m): m for m in empty_matches}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result['success']:
                success += 1
                if completed % 20 == 0 or completed == len(empty_matches):
                    print('[%d/%d] %s/%s: OK (%d -> %d bytes)' % (
                        completed, len(empty_matches), result['date'], result['name'],
                        result['old_size'], result['new_size']
                    ))
            else:
                failed.append(result)
                print('[%d/%d] %s/%s: FAIL (%d -> %d bytes, %s)' % (
                    completed, len(empty_matches), result['date'], result['name'],
                    result['old_size'], result.get('new_size', 0),
                    result.get('error', 'rc=%d' % result.get('returncode', -1))
                ))
    
    print('\n' + '='*60)
    print('重跑完成！')
    print('成功: %d/%d (%.1f%%)' % (success, len(empty_matches), success*100.0/len(empty_matches)))
    print('失败: %d/%d (%.1f%%)' % (len(failed), len(empty_matches), len(failed)*100.0/len(empty_matches)))
    
    if failed:
        # 分析失败原因
        print('\n失败分析:')
        fail_league_stats = {}
        for f in failed:
            league = f['league']
            if league not in fail_league_stats:
                fail_league_stats[league] = []
            fail_league_stats[league].append(f)
        
        for league, items in sorted(fail_league_stats.items(), key=lambda x: -len(x[1])):
            print('  %s: %d场' % (league, len(items)))
            for item in items[:3]:
                print('    - %s/%s (new_size=%d)' % (item['date'], item['name'], item.get('new_size', 0)))

if __name__ == '__main__':
    main()
