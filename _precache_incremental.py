#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增量更新联赛缓存 — 只抓每队最近N场，只富集新增比赛，合并写回

用法：
    python3 -u _precache_incremental.py                 # 更新全部主要联赛
    python3 -u _precache_incremental.py 英冠 日乙        # 指定联赛

原理：
    1. 读旧缓存，拿到已有 FIXTUREID 集合
    2. _get_league_teams 拿球队 → 每队 _fetch_team_matches_ajax(records=30) 只抓近期
    3. 过滤出本联赛 + FIXTUREID 不在旧缓存的 = 新增比赛
    4. 只对新增比赛 _fetch_match_odds 富集
    5. 合并旧缓存 + 新增比赛，写回
"""
import sys, os, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed

SD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SD)
import precache_leagues as P

MAJOR_LEAGUES = [
    '英超Premier League', '西甲La Liga', '意甲Serie A', '德甲Bundesliga', '法甲',
    '欧冠Champions League', '欧罗巴UEFA Europa League', '欧协联',
    '英冠', '英甲', '英联杯', '英足总杯',
    # 二级联赛（竞彩常开）
    '德乙', '法乙', '荷乙',
    '日职', '日乙', 'K1联赛', '澳超', '沙特职业联赛', '中超Chinese Super League', '亚冠',
    '巴甲', '阿甲', '美职联',
    '瑞超', '挪超', '芬兰超级联赛',
    '葡超', '荷甲', '比甲', '苏超', '土超', '瑞士超',
    '爱超', '捷甲', '罗甲', '克罗甲', '保超', '匈甲', '斯伐超', '希腊超A',
]

RECORDS = 30      # 每队抓取最近场数

def _fetch_retry(fid, tries=3):
    """_fetch_match_odds 带重试：瞬时限流/超时失败后重试"""
    import time as _t
    for i in range(tries):
        try:
            r = P._fetch_match_odds(fid)
            if r:
                oe = r.get('odds_europe') or {}
                cos = oe.get('companies') or []
                jc = oe.get('jc') if isinstance(oe.get('jc'), dict) else None
                av = oe.get('av') if isinstance(oe.get('av'), dict) else None
                # 完整性校验：欧赔companies + jc + av + 亚盘 必须有；让球可选（部分场次源站rangqiu无数据）
                if cos and jc and av and r.get('odds_asian'):
                    return r
            if i < tries - 1:
                _t.sleep(3 * (i + 1))
        except Exception:
            if i < tries - 1:
                _t.sleep(3 * (i + 1))
    return None
ENRICH_WORKERS = 1  # 并发1防EdgeOne JS challenge(2026-09-09实测3并发~140场触发封禁)
SLEEP_BETWEEN_TEAMS = 0.15

# 500.com页面联赛名 → 缓存联赛名（页面叫法不同但同一赛事）
LEAGUE_NAME_MAP = {
    '亚冠': '亚冠杯',      # 500.com 2025/26赛季叫"亚冠杯"，缓存/竞彩叫"亚冠"
}
RECORDS_OVERRIDE = {
    '亚冠': 100,           # 亚冠比赛稀疏（每队赛季仅数场），30场不够需100
}


def _site_blocked():
    try:
        r = P.sess.get('https://liansai.500.com/zuqiu-9110/', timeout=12)
        return r.status_code != 200
    except Exception:
        return True


def _get_team_ids_retry(league):
    """获取球队ID，503限流时等待退避重试。探测用目标联赛页，避免误判"""
    for attempt in range(4):
        team_ids, league_id = P._get_league_teams(league, '', '')
        if team_ids:
            return team_ids, league_id
        # 直接探测目标联赛页的状态码
        lid = league_id or P.LEAGUE_ID_MAP.get(league, '')
        blocked = True
        if lid:
            try:
                r = P.sess.get('https://liansai.500.com/zuqiu-{}/'.format(lid), timeout=12)
                blocked = r.status_code != 200
            except Exception:
                blocked = True
        else:
            blocked = _site_blocked()
        print('[INC] {}: 球队ID为空(第{}次) 目标页{}限流={}'.format(
            league, attempt + 1, lid, blocked), flush=True)
        if blocked:
            wait = 120 + attempt * 90
            print('[INC]   等待{}s后重试'.format(wait), flush=True)
            time.sleep(wait)
        else:
            print('[INC]   目标页正常但无球队ID（联赛页无数据？）', flush=True)
            return None, None
    return None, None


def _scrape_recent(league, team_ids, is_cup):
    """只抓每队最近RECORDS场比赛（1轮，不反向发现）"""
    records = RECORDS_OVERRIDE.get(league, RECORDS)
    page_league = LEAGUE_NAME_MAP.get(league, league)
    all_matches = []
    seen_fid = set()
    for tid in sorted(set(team_ids)):
        ml = P._fetch_team_matches_ajax(tid, records=records)
        for m in ml:
            fid = str(m.get('FIXTUREID', ''))
            if fid and fid not in seen_fid and fid not in P.DEAD_FIDS:
                seen_fid.add(fid)
                all_matches.append(m)
        time.sleep(SLEEP_BETWEEN_TEAMS)
    # 过滤本联赛（用页面联赛名匹配）
    filtered = []
    for d in all_matches:
        ln = d.get('SIMPLEGBNAME', '')
        if not ln or not P._league_match(ln, page_league):
            continue
        fid = str(d.get('FIXTUREID', ''))
        if not fid:
            continue
        filtered.append(d)
    return filtered


def incremental_update(league):
    cache_path = os.path.join(P.CACHE_DIR, '{}.json'.format(league))
    # 读旧缓存
    old = {'all_matches': [], 'league_id': None}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                old = json.load(f)
        except Exception as e:
            print('[INC] {}: 旧缓存读取失败 {}'.format(league, e), flush=True)
    old_fids = set(str(m.get('FIXTUREID', '')) for m in old.get('all_matches', []) if m.get('FIXTUREID'))
    old_count = len(old.get('all_matches', []))
    old_enriched = old.get('enriched_date') or old.get('enriched')

    team_ids, league_id = _get_team_ids_retry(league)
    if not team_ids:
        return 'no_team_ids'

    is_cup = any(c in league for c in ['杯', 'Cup', 'cup', '欧冠', '欧联', '欧罗巴', '欧协', '解放者', '冠军'])
    recent = _scrape_recent(league, team_ids, is_cup)

    # 新增 = 不在旧缓存里
    new_matches = [m for m in recent if str(m.get('FIXTUREID', '')) not in old_fids]
    # 已有但旧缓存缺富集字段的（从旧缓存查真缺，AJAX 记录永远无 odds 不能作判据）
    to_enrich_fids = []
    for _m in old.get('all_matches', []):
        _fid = str(_m.get('FIXTUREID', ''))
        if not _fid or _fid in P.DEAD_FIDS:
            continue
        # 真空壳 = 无亚盘 且 (无 companies 且 jc 无值)；av 顶级缺失不算缺（工具可从 companies fallback）
        _oe = _m.get('odds_europe') or {}
        _cos = _oe.get('companies') or []
        _jc_lw = ((_oe.get('jc') or {}).get('lw')) if isinstance(_oe.get('jc'), dict) else None
        if not _m.get('odds_asian') or (not _cos and not _jc_lw):
            to_enrich_fids.append(_fid)
    to_enrich_fids = list(dict.fromkeys(to_enrich_fids))
    # 去重合并：旧缓存为底，新增直接加
    merged = list(old.get('all_matches', []))
    seen = set(old_fids)
    for m in new_matches:
        fid = str(m.get('FIXTUREID', ''))
        if fid and fid not in seen:
            seen.add(fid)
            merged.append(m)
    # 按日期排序（MATCHDATE 降序，新的在前，仅新增段）
    P._add_computed_fields(new_matches)

    print('[INC] {}: 旧缓存{}场 → 新增{}场，补富集{}场，合计{}场'.format(
        league, old_count, len(new_matches), len(to_enrich_fids), len(merged)), flush=True)

    # 富集对象 = 新增 + 补富集 FID 并集
    enrich_fids = [str(m.get('FIXTUREID', '')) for m in new_matches if str(m.get('FIXTUREID', ''))]
    enrich_fids = list(dict.fromkeys(enrich_fids + to_enrich_fids))
    # 分批防 EdgeOne：单批上限（PRECACHE_BATCH_LIMIT），跑完一批歇一批避免~300请求触发封禁
    _lim = int(os.environ.get('PRECACHE_BATCH_LIMIT', '0') or 0)
    if _lim > 0 and len(enrich_fids) > _lim:
        print('[INC] {}: 批量上限{}场（实际{}），本批只补前{}场'.format(
            league, _lim, len(enrich_fids), _lim), flush=True)
        enrich_fids = enrich_fids[:_lim]
    if enrich_fids:
        print('[INC] {}: 富集{}场（新增{} + 补富集{}）...'.format(
            league, len(enrich_fids), len(new_matches), len(to_enrich_fids)), flush=True)
        enriched = {}
        errors = 0
        with ThreadPoolExecutor(max_workers=ENRICH_WORKERS) as ex:
            fut_map = {ex.submit(_fetch_retry, fid): fid for fid in enrich_fids}
            for fut in as_completed(fut_map):
                fid = fut_map[fut]
                try:
                    res = fut.result()
                    if res:
                        enriched[fid] = res
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
        for m in merged:
            fid = str(m.get('FIXTUREID', ''))
            if fid in enriched:
                odds = enriched[fid]
                for k in ('odds_europe', 'odds_handicap', 'odds_asian'):
                    if odds.get(k):
                        m[k] = odds[k]
        print('[INC] {}: 富集完成 成功{} 失败{}'.format(league, len(enriched), errors), flush=True)

    # 写回（保留旧字段）
    cache_data = {
        'league': league,
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'match_count': len(merged),
        'league_id': league_id or old.get('league_id'),
        'team_ids': list(team_ids),
        'matches_with_scores': sum(1 for m in merged if m.get('_computed')),
        'all_matches': merged,
        'cache_mode': 'incremental',
    }
    if old_enriched:
        cache_data['enriched'] = old_enriched
    P._backup_cache(cache_path)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print('[INC] {}: 写回 ✓（{}场）'.format(league, len(merged)), flush=True)
    return 'ok'


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        run_list = sys.argv[1:]
    else:
        run_list = MAJOR_LEAGUES
    print('[INC] ===== 增量更新启动: {}个联赛 ====='.format(len(run_list)), flush=True)
    ok, fail = [], []
    for i, league in enumerate(run_list, 1):
        print('[INC] [{}/{}] {} ...'.format(i, len(run_list), league), flush=True)
        # 每次请求前探测，避免触发反爬
        if _site_blocked():
            print('[INC]   站点限流，等待120s', flush=True)
            time.sleep(120)
        try:
            rc = incremental_update(league)
            if rc == 'ok':
                ok.append(league)
            else:
                fail.append(league)
        except Exception as e:
            import traceback
            traceback.print_exc()
            fail.append(league)
        time.sleep(5)
    print('[INC] ===== 完成: 成功{} 失败{} ====='.format(len(ok), len(fail)), flush=True)
    if fail:
        print('[INC] 失败: {}'.format(fail), flush=True)


if __name__ == '__main__':
    main()
