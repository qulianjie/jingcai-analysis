#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""联赛历史数据预缓存 — 全局共享缓存，3天刷新一次

使用方式：
    python precache_leagues.py 2026-05-19      # 缓存指定日期的所有联赛

缓存路径：data/league_cache/{league}.json（全局共享，不按天分目录）
刷新周期：3天（文件mtime），超时重爬
并发安全：.lockdir 目录锁，15s超时回退到联网
"""
import sys, os, json, re, time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
CACHE_DIR = os.path.join(SCRIPT_DIR, 'data', 'league_cache')
CACHE_TTL_DAYS = 3

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# 导入联赛工具
sys.path.insert(0, SCRIPT_DIR)
from _league_util import _league_match, LEAGUE_ID_MAP

# 杯赛列表
CUP_NAMES = ['欧罗巴', '欧联', '欧协联', '解放者杯', '南美解放者杯', '欧冠', 
             '欧洲冠军联赛', '德国杯', '西班牙国王杯', '意大利杯', '法国杯',
             '英格兰足总杯', '英格兰联赛杯', '葡超杯', '巴甲杯', '巴西杯',
             '阿根廷杯', '哥伦杯', '厄瓜杯', '日本天皇杯', '亚冠', '亚足联冠军', '非洲冠军杯']


def _acquire_lock(lock_path, timeout=15):
    """获取目录锁，timeout秒内重试"""
    for _ in range(timeout * 2):
        try:
            os.mkdir(lock_path)
            return True
        except FileExistsError:
            time.sleep(0.5)
    return False


def _is_cache_fresh(cache_path):
    """检查缓存是否在3天有效期内"""
    if not os.path.exists(cache_path):
        return False
    try:
        mtime = os.path.getmtime(cache_path)
        age_days = (time.time() - mtime) / 86400
        return age_days < CACHE_TTL_DAYS
    except:
        return False


def _load_matches(date_str):
    """加载指定日期的所有比赛"""
    matches_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    search_paths = [
        matches_file,
        os.path.join(TASKS_DIR, date_str, 'matches.json'),
        os.path.join(TASKS_DIR, 'matches_data.json'),
    ]
    for fpath in search_paths:
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'matches' in data and isinstance(data['matches'], list):
                return data['matches']
            if 'groups' in data and isinstance(data['groups'], dict):
                all_matches = []
                for gn, gd in data['groups'].items():
                    if isinstance(gd, dict) and 'matches' in gd:
                        all_matches.extend(gd['matches'])
                if all_matches:
                    return all_matches
    return []


def _get_league_teams(league, home_id, away_id):
    """获取联赛的球队列表（与 step8 逻辑一致）"""
    team_ids = set()
    league_id = LEAGUE_ID_MAP.get(league, '')
    
    if league_id:
        league_url = 'https://liansai.500.com/zuqiu-{}/'.format(league_id)
        try:
            resp = sess.get(league_url, timeout=15)
            resp.encoding = 'gbk'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                m = re.search(r'/team/(\d+)', href)
                if m and '/teamfixture/' not in href:
                    team_ids.add(m.group(1))
        except Exception as e:
            pass

    if len(team_ids) == 0:
        team_ids = {str(home_id), str(away_id)}

    team_ids.discard('')
    return list(team_ids), league_id


def _fetch_team_matches_ajax(tid, records=100):
    """通过AJAX接口获取球队历史比赛（最多100场，比HTML页面30场多3倍）
    
    使用liansai.500.com的AJAX接口，支持records=10/30/50/100
    返回原始JSON列表，含FIXTUREID/HOMESCORE/AWAYSCORE/HANDICAPLINE等字段
    """
    url = 'https://liansai.500.com/index.php?c=teams&a=ajax_fixture'
    params = {'hoa': '0', 'records': str(records), 'tid': str(tid)}
    try:
        resp = requests.get(url, params=params, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://liansai.500.com/team/{}/teamfixture/'.format(tid),
            'X-Requested-With': 'XMLHttpRequest',
        })
        resp.encoding = 'gbk'
        data = resp.json()
        return data.get('list', [])
    except Exception as e:
        return []


def _scrape_league_matches(league, team_ids, is_cup):
    """抓取联赛所有比赛数据（使用AJAX接口，每队最多100场）"""
    all_matches = []
    seen_fid = set()

    if is_cup:
        team_set = set(team_ids)
        for iteration in range(2):
            round_teams = sorted(team_set)
            prev_count = len(team_set)
            for tid in round_teams:
                match_list = _fetch_team_matches_ajax(tid)
                for m in match_list:
                    fid = str(m.get('FIXTUREID', ''))
                    if fid and fid not in seen_fid:
                        seen_fid.add(fid)
                        all_matches.append(m)
                        team_set.add(str(m.get('HOMETEAMID', '')))
                        team_set.add(str(m.get('AWAYTEAMID', '')))
                time.sleep(0.1)
            new_count = len(team_set) - prev_count
            if new_count == 0:
                break
        team_set.discard('')
        return all_matches, list(team_set)
    else:
        # 2轮发现：从已知球队的反向发现对手ID，应对联赛页面展示不全的情况（如澳超只列2队）
        team_set = set(team_ids)
        for iteration in range(2):
            round_teams = sorted(team_set)
            prev_count = len(team_set)
            for tid in round_teams:
                match_list = _fetch_team_matches_ajax(tid)
                for m in match_list:
                    fid = str(m.get('FIXTUREID', ''))
                    if fid and fid not in seen_fid:
                        seen_fid.add(fid)
                        all_matches.append(m)
                        team_set.add(str(m.get('HOMETEAMID', '')))
                        team_set.add(str(m.get('AWAYTEAMID', '')))
                time.sleep(0.2)
            new_count = len(team_set) - prev_count
            if new_count == 0:
                break
        team_set.discard('')
        return all_matches, list(team_set)


def _lookup_team_ids_from_fid(fid, home_name, away_name):
    """通过 FID 从500.com yazhi页面提取球队ID"""
    home_id = ''
    away_id = ''
    try:
        url = 'https://odds.500.com/fenxi/yazhi-{}.shtml'.format(fid)
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 2:
                    continue
                name_col = tds[1].get_text().strip() if len(tds) > 1 else ''
                if home_name and home_name in name_col:
                    for a in (tds[1].find_all('a', href=True) if len(tds) > 1 else []):
                        tm = re.search(r'/team/(\d+)/', a.get('href', ''))
                        if tm:
                            home_id = tm.group(1)
                            break
                if away_name and away_name in name_col:
                    for a in (tds[1].find_all('a', href=True) if len(tds) > 1 else []):
                        tm = re.search(r'/team/(\d+)/', a.get('href', ''))
                        if tm:
                            away_id = tm.group(1)
                            break
    except Exception as e:
        pass
    if not home_id or not away_id:
        try:
            url2 = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid)
            resp2 = sess.get(url2, timeout=15)
            resp2.encoding = 'gbk'
            soup2 = BeautifulSoup(resp2.text, 'html.parser')
            team_links = []
            for a in soup2.find_all('a', href=True):
                href = a.get('href', '')
                tm = re.search(r'/team/(\d+)/', href)
                if tm:
                    atxt = a.get_text().strip()
                    if atxt:
                        team_links.append((tm.group(1), atxt))
            seen = set()
            for tid, txt in team_links:
                if tid not in seen:
                    seen.add(tid)
                    if not home_id:
                        home_id = tid
                    elif home_id != tid and not away_id:
                        away_id = tid
                        break
        except:
            pass
    return home_id, away_id



# ============================================================
# 新功能：让球结果计算 + 盘路方向 + 缓存富集
# ============================================================

def _compute_letball_result(home_score, away_score, handicap_line):
    """根据实际比分+让球数，计算让球后结果"""
    try:
        hs = int(home_score) if home_score else 0
        as_ = int(away_score) if away_score else 0
        hl = float(handicap_line) if handicap_line else 0
    except (ValueError, TypeError):
        return None
    letball_home = hs + hl
    if letball_home > as_: return '主胜'
    elif letball_home < as_: return '客胜'
    else: return '平局'

def _compute_match_result(home_score, away_score):
    try:
        hs = int(home_score) if home_score else 0
        as_ = int(away_score) if away_score else 0
    except: return None
    if hs > as_: return '主胜'
    elif hs < as_: return '客胜'
    else: return '平局'

def _odds_direction(init_vals, live_vals):
    result = ''
    for a, b in zip(init_vals, live_vals):
        if b > a + 0.01: result += chr(0x2B06)
        elif b < a - 0.01: result += chr(0x2B07)
        else: result += chr(0x27A1)
    return result

def _fetch_match_odds(fid):
    """获取单场比赛的完整 odds 数据（欧赔+让球+亚盘+庄家）"""
    result = {'fid': fid}
    # 1. 欧赔
    try:
        url = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid)
        resp = requests.get(url, timeout=8, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        companies = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                nums = []
                for idx in [3, 4, 5, 6, 7, 8]:
                    val = tds[idx].get_text().strip().replace(chr(160), '')
                    try: nums.append(float(val))
                    except: pass
                if len(nums) >= 6:
                    companies.append({
                        'row_num': td0, 'name': td1,
                        'iw': nums[0], 'id': nums[1], 'il': nums[2],
                        'lw': nums[3], 'ld': nums[4], 'll': nums[5]
                    })
                if len(companies) >= 15: break
            if len(companies) >= 15: break
        jc = iw = av = None
        for c in companies:
            if c['row_num'] == '1': jc = c
            elif c['row_num'] == '6': iw = c
            elif chr(24179)+chr(22343)+chr(20540) in c.get('name',''): av = c
        result['odds_europe'] = {
            'jc': {k:c[k] for k in ('iw','id','il','lw','ld','ll')} if jc else None,
            'iw': {k:c[k] for k in ('iw','id','il','lw','ld','ll')} if iw else None,
            'av': {k:c[k] for k in ('iw','id','il','lw','ld','ll')} if av else None,
            'dir_jc': _odds_direction(
                [jc['iw'],jc['id'],jc['il']],[jc['lw'],jc['ld'],jc['ll']]) if jc else '',
            'companies': [{'name':c.get('name',''),'init':[c.get('iw'),c.get('id'),c.get('il')],
                'live':[c.get('lw'),c.get('ld'),c.get('ll')],
                'dir':_odds_direction([c.get('iw',0),c.get('id',0),c.get('il',0)],
                    [c.get('lw',0),c.get('ld',0),c.get('ll',0)])} for c in companies[:10]]
        }
    except: result['odds_europe'] = None
    # 2. 让球
    try:
        url_rq = 'https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid)
        resp2 = requests.get(url_rq, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        resp2.encoding = 'gbk'
        soup2 = BeautifulSoup(resp2.text, 'html.parser')
        for table in soup2.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td2 = tds[2].get_text().strip().replace(chr(160), '')
                if td0 == '1':
                    nums = []
                    for idx in [4, 5, 6, 7, 8, 9]:
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(val))
                        except: pass
                    if len(nums) >= 6:
                        result['odds_handicap'] = {
                            'jc': {'handicap': td2, 'iw': nums[0], 'id': nums[1], 'il': nums[2],
                                'lw': nums[3], 'ld': nums[4], 'll': nums[5],
                                'dir': _odds_direction(nums[:3], nums[3:6])}
                        }
                    break
                if result.get('odds_handicap'): break
            if result.get('odds_handicap'): break
    except: result['odds_handicap'] = None
    # 3. 亚盘
    try:
        url_yz = 'https://odds.500.com/fenxi/yazhi-{}.shtml'.format(fid)
        resp3 = requests.get(url_yz, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        resp3.encoding = 'gbk'
        soup3 = BeautifulSoup(resp3.text, 'html.parser')
        yz_list = []
        for table in soup3.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0.isdigit() and int(td0) in (1, 2, 3):
                    name = tds[1].get_text().strip()
                    iiw = il_text = iil = liw = ll_text = lil = ''
                    for idx in range(len(tds)):
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        if idx == 3:
                            m = __import__('re').search(r'([\d\.]+)', val)
                            if m: iiw = m.group(1)
                        elif idx == 4: il_text = val
                        elif idx == 5:
                            m = __import__('re').search(r'([\d\.]+)', val)
                            if m: iil = m.group(1)
                        elif idx == 9:
                            m = __import__('re').search(r'([\d\.]+)', val)
                            if m: liw = m.group(1)
                        elif idx == 10: ll_text = val
                        elif idx == 11:
                            m = __import__('re').search(r'([\d\.]+)', val)
                            if m: lil = m.group(1)
                    yz_list.append({
                        'name': name,
                        'init_pan': il_text, 'init_water_high': iiw, 'init_water_low': iil,
                        'live_pan': ll_text, 'live_water_high': liw, 'live_water_low': lil,
                    })
                    if len(yz_list) >= 3: break
                if len(yz_list) >= 3: break
            if len(yz_list) >= 3: break
        result['odds_asian'] = yz_list if yz_list else None
    except: result['odds_asian'] = None
    return result

def _enrich_cache(cache_path, max_workers=20):
    """富集缓存：为所有有FID的比赛补充odds数据"""
    if not os.path.exists(cache_path):
        print('[ENRICH] 缓存不存在: {}'.format(cache_path))
        return False
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    league = cache_data.get('league', '?')
    matches = cache_data.get('all_matches', [])
    to_enrich = [str(m.get('FIXTUREID','')) for m in matches 
                 if str(m.get('FIXTUREID','')) and not m.get('odds_europe')]
    if not to_enrich:
        print('[ENRICH] {}: 没有需要富集的比赛'.format(league))
        return True
    print('[ENRICH] {}: 富集中 {} 场比赛...'.format(league, len(to_enrich)))
    enriched = {}; completed = 0; errors = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fut_map = {executor.submit(_fetch_match_odds, fid): fid for fid in to_enrich}
        for fut in as_completed(fut_map):
            fid = fut_map[fut]
            try:
                enriched[fid] = fut.result()
                completed += 1
            except: errors += 1
            if (completed + errors) % 20 == 0:
                print('[ENRICH] {}: {}/{} (失败{})'.format(league, completed+errors, len(to_enrich), errors))
    updated = 0
    for m in matches:
        fid = str(m.get('FIXTUREID', ''))
        if fid in enriched:
            odds = enriched[fid]
            for key in ('odds_europe', 'odds_handicap', 'odds_asian'):
                if odds.get(key) is not None: m[key] = odds[key]
            updated += 1
            # 每50个FID增量保存，超时中断也不丢进度
            if updated % 50 == 0:
                cache_data['all_matches'] = matches
                cache_data['enriched'] = False
                cache_data['enriched_count'] = updated
                with open(cache_path, 'w', encoding='utf-8') as ft:
                    json.dump(cache_data, ft, ensure_ascii=False)
    cache_data['enriched'] = True
    cache_data['enriched_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    cache_data['enriched_count'] = updated
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print('[ENRICH] {}: 富集完成，{}场更新 (成功{}/失败{})'.format(league, updated, completed, errors))
    return True

def _add_computed_fields(league_filtered):
    """为缓存中的每场比赛添加计算结果字段"""
    for m in league_filtered:
        try:
            hs = m.get('HOMESCORE', '')
            as_ = m.get('AWAYSCORE', '')
            if hs == '' or as_ == '': continue
            hs = int(hs); as_ = int(as_)
            hl = m.get('HANDICAPLINE')
            hl = float(hl) if hl else 0
        except: continue
        m['_computed'] = {
            'match_result': _compute_match_result(hs, as_),
            'letball_result': _compute_letball_result(hs, as_, hl),
            'home_score': hs, 'away_score': as_,
        }

def _list_cached_leagues():
    if not os.path.exists(CACHE_DIR): return []
    return sorted([f[:-5] for f in os.listdir(CACHE_DIR) if f.endswith('.json')])


def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    # 检查 --enrich 模式
    enrich_mode = '--enrich' in sys.argv
    if enrich_mode:
        enrich_target = None
        for i, arg in enumerate(sys.argv):
            if arg == '--enrich' and i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('-'):
                enrich_target = sys.argv[i+1]
                break
        if enrich_target:
            cp = os.path.join(CACHE_DIR, '{}.json'.format(enrich_target))
            if os.path.exists(cp): _enrich_cache(cp)
            else: print('[PRECACHE] 未找到联赛缓存: {}'.format(enrich_target))
        else:
            for league in _list_cached_leagues():
                _enrich_cache(os.path.join(CACHE_DIR, '{}.json'.format(league)))
        return
    
    # == --precache-all 模式：主动缓存所有58个联赛 ==
    if '--precache-all' in sys.argv:
        print('[PRECACHE] ===== 启动全联赛预缓存 =====')
        os.makedirs(CACHE_DIR, exist_ok=True)
        # 从LEAGUE_ID_MAP遍历所有联赛
        league_names = list(LEAGUE_ID_MAP.keys())
        print('[PRECACHE] 共{}个联赛待处理'.format(len(league_names)))
        for league in league_names:
            cache_path = os.path.join(CACHE_DIR, '{}.json'.format(league))
            if _is_cache_fresh(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                print('[PRECACHE] {}: 缓存有效（{}场），跳过'.format(
                    league, cached.get('match_count', '?')))
                continue
            print('[PRECACHE] {}: 开始爬取...'.format(league))
            is_cup = any(c in league for c in ['杯', 'Cup', 'cup', '欧冠', '欧联', '欧罗巴', '欧协', '解放者', '冠军'])
            lock_path = cache_path + '.lockdir'
            if not _acquire_lock(lock_path):
                print('[PRECACHE] {}: 获取锁超时，跳过'.format(league))
                continue
            try:
                if _is_cache_fresh(cache_path):
                    print('[PRECACHE] {}: 锁后检测到缓存已更新，跳过'.format(league))
                    continue
                team_ids, league_id = _get_league_teams(league, '', '')
                if not team_ids:
                    print('[PRECACHE] {}: 未找到球队ID，跳过'.format(league))
                    continue
                all_matches, final_teams = _scrape_league_matches(league, team_ids, is_cup)
                seen_fid = set()
                league_filtered = []
                for d in all_matches:
                    league_name = d.get('SIMPLEGBNAME', '')
                    if not league_name or not _league_match(league_name, league):
                        continue
                    fid = str(d.get('FIXTUREID', ''))
                    if not fid or fid in seen_fid:
                        continue
                    seen_fid.add(fid)
                    league_filtered.append(d)
                _add_computed_fields(league_filtered)
                with_scores = sum(1 for m in league_filtered if m.get('_computed'))
                cache_data = {
                    'league': league, 'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'match_count': len(league_filtered), 'league_id': league_id,
                    'team_ids': final_teams, 'matches_with_scores': with_scores,
                    'all_matches': league_filtered, 'cache_mode': 'precache_all',
                }
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print('[PRECACHE] {}: {}场（{}场有比分）→ 缓存 ✓'.format(
                    league, len(league_filtered), with_scores))
            except Exception as e:
                print('[PRECACHE] {}: 爬取失败: {}'.format(league, e))
            finally:
                try:
                    if os.path.exists(lock_path): os.rmdir(lock_path)
                except: pass
        print('[PRECACHE] ===== 全联赛预缓存完成 ✓ =====')
        return
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        date_str = sys.argv[1]

    matches = _load_matches(date_str)
    if not matches:
        print('[PRECACHE] 未找到比赛数据: {}'.format(date_str))
        return

    print('[PRECACHE] 比赛总数: {}'.format(len(matches)))

    # 分组（按联赛）
    leagues = {}
    for m in matches:
        league = m.get('league', '')
        if not league:
            continue
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(m)

    unique_leagues = list(leagues.keys())
    print('[PRECACHE] 唯一联赛数: {}'.format(len(unique_leagues)))
    for league in unique_leagues:
        print('[PRECACHE]   {}: {}场'.format(league, len(leagues[league])))

    # 全局缓存目录
    os.makedirs(CACHE_DIR, exist_ok=True)
    print('[PRECACHE] 缓存目录: {}'.format(CACHE_DIR))

    # 预检查：所有联赛缓存是否都新鲜
    all_fresh = True
    for league in unique_leagues:
        cache_path = os.path.join(CACHE_DIR, '{}.json'.format(league))
        if not _is_cache_fresh(cache_path):
            all_fresh = False
            print('[PRECACHE]   {}: 缓存过期或无缓存'.format(league))
        else:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            print('[PRECACHE]   {}: 缓存有效（{}场，{}）'.format(
                league, cached.get('match_count', '?'), cached.get('date', '?')))

    if all_fresh:
        print('[PRECACHE] 所有联赛缓存有效（<3天内），跳过爬取 ✓')
        return

    # 逐联赛处理（只处理过期/缺失的）
    for league in unique_leagues:
        cache_path = os.path.join(CACHE_DIR, '{}.json'.format(league))

        if _is_cache_fresh(cache_path):
            continue  # 缓存有效，跳过

        print('[PRECACHE] {}: 开始爬取...'.format(league))

        is_cup = any(c in league for c in ['杯', 'Cup', 'cup', '欧冠', '欧联', '欧罗巴', '欧协', '解放者', '冠军'])
        home_id = leagues[league][0].get('home_id', '')
        away_id = leagues[league][0].get('away_id', '')

        # 回退：查找球队ID
        if not home_id or not away_id:
            fid = leagues[league][0].get('fid', '')
            home_name = leagues[league][0].get('home', '')
            away_name = leagues[league][0].get('away', '')
            if fid:
                home_id, away_id = _lookup_team_ids_from_fid(fid, home_name, away_name)

        # 加锁爬取+写缓存
        lock_path = cache_path + '.lockdir'
        if not _acquire_lock(lock_path):
            print('[PRECACHE] {}: 获取锁超时，跳过'.format(league))
            continue

        try:
            # 双重检查：锁后可能有别人写完了
            if _is_cache_fresh(cache_path):
                print('[PRECACHE] {}: 锁后检测到缓存已更新，跳过'.format(league))
                continue

            if is_cup:
                team_ids_for_cup = [home_id, away_id] if home_id and away_id else team_ids
                all_matches, final_teams = _scrape_league_matches(league, team_ids_for_cup, is_cup)
            else:
                team_ids, league_id = _get_league_teams(league, home_id, away_id)
                all_matches, final_teams = _scrape_league_matches(league, team_ids, is_cup)

            # 筛选同联赛 + 去重
            seen_fid = set()
            league_filtered = []
            for d in all_matches:
                league_name = d.get('SIMPLEGBNAME', '')
                if not league_name or not _league_match(league_name, league):
                    continue
                fid = str(d.get('FIXTUREID', ''))
                if not fid or fid in seen_fid:
                    continue
                seen_fid.add(fid)
                league_filtered.append(d)

            _add_computed_fields(league_filtered)
            with_scores = sum(1 for m in league_filtered if m.get('_computed'))

            cache_data = {
                'league': league,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'match_count': len(league_filtered),
                'league_id': LEAGUE_ID_MAP.get(league, ''),
                'team_ids': final_teams,
                'matches_with_scores': with_scores,
                'all_matches': league_filtered,
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            print('[PRECACHE] {}: {}场（{}场有比分）→ 缓存 {}'.format(
                league, len(league_filtered), with_scores, cache_path))

            # === 缓存质量核查 + 修正 ===
            if len(league_filtered) == 0:
                print('[PRECACHE] ⚠️ {}: 缓存为空，尝试重爬一次...'.format(league))
                time.sleep(2)
                try:
                    if is_cup:
                        team_ids2_cup = [home_id, away_id] if home_id and away_id else team_ids
                        all_matches2, final_teams2 = _scrape_league_matches(league, team_ids2_cup, is_cup)
                    else:
                        team_ids2, league_id2 = _get_league_teams(league, home_id, away_id)
                        all_matches2, final_teams2 = _scrape_league_matches(league, team_ids2, is_cup)
                    seen_fid2 = set()
                    league_filtered2 = []
                    for d in all_matches2:
                        league_name = d.get('SIMPLEGBNAME', '')
                        if not league_name or not _league_match(league_name, league):
                            continue
                        fid2 = str(d.get('FIXTUREID', ''))
                        if not fid2 or fid2 in seen_fid2:
                            continue
                        seen_fid2.add(fid2)
                        league_filtered2.append(d)
                    if len(league_filtered2) > 0:
                        cache_data2 = {
                            'league': league,
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'match_count': len(league_filtered2),
                            'league_id': LEAGUE_ID_MAP.get(league, ''),
                            'team_ids': final_teams2,
                            'all_matches': league_filtered2,
                        }
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            json.dump(cache_data2, f, ensure_ascii=False, indent=2)
                        print('[PRECACHE] ✅ {}: 重爬成功，{}场'.format(league, len(league_filtered2)))
                        league_filtered = league_filtered2
                    else:
                        print('[PRECACHE] ❌ {}: 重爬仍为空，请检查联赛名映射({})或源站是否可访问'.format(league, league))
                except Exception as e2:
                    print('[PRECACHE] ❌ {}: 重爬失败: {}'.format(league, e2))




        except Exception as e:
            print('[PRECACHE] {}: 爬取失败: {}'.format(league, e))
        finally:
            try:
                if os.path.exists(lock_path):
                    os.rmdir(lock_path)
            except:
                pass

    print('[PRECACHE] 完成 ✓')


if __name__ == '__main__':
    main()
