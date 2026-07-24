# -*- coding: utf-8 -*-
"""
将模式匹配报告同步到 Notion 的「备注」属性列
用法: python notion_pattern_sync.py [2026-05-23]
"""

import os, sys, json, re, urllib.request
from datetime import datetime

try:
    from _util import ensure_utf8_stdout
    ensure_utf8_stdout()
except: pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'match_patterns_report.json')
DS_ID = "35491ad7-17ba-81df-b58c-000ba04f22b7"
TOKEN = "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"


def notion_req(method, endpoint, body=None):
    url = 'https://api.notion.com/v1/' + endpoint
    payload = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=payload, headers={
        'Authorization': 'Bearer ' + TOKEN,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    }, method=method)
    try:
        resp = urllib.request.urlopen(req).read().decode('utf-8')
        return json.loads(resp)
    except urllib.error.HTTPError as e:
        print('  HTTP %d: %s' % (e.code, e.read().decode('utf-8')[:100]))
        return None


def format_remark(match_data):
    """把匹配结果格式化成备注文本"""
    lines = []
    lines.append('📊 模式匹配结果')
    lines.append('')

    # 按结果分组，取每个结果方向的最佳模式
    by_result = {}
    for h in match_data['hits']:
        r = h['result']
        if r not in by_result: by_result[r] = []
        by_result[r].append(h)

    for result in ['胜', '平', '负']:
        if result not in by_result: continue
        hlist = by_result[result]
        hlist.sort(key=lambda x: (-x['lift'], -x['total']))
        best = hlist[0]

        combo = ' / '.join('%s=%s' % (k.split('_')[0] if len(k) > 6 else k, v)
                          for k, v in sorted(best['combo'].items()))
        combo = combo[:50]

        lines.append('[%s] %d%% (x%.1f, %d/%d) %s' % (
            result, best['pct']*100, best['lift'], best['correct'], best['total'], combo))

        if len(hlist) > 1:
            extra = hlist[1]
            lines.append('  + %d%% (x%.1f, %d/%d)' % (
                extra['pct']*100, extra['lift'], extra['correct'], extra['total']))

    return '\n'.join(lines)


def find_notion_pages_by_date(date_str):
    """查找指定日期的所有 Notion 比赛页面"""
    all_pages = []
    cursor = None
    while True:
        body = {
            'filter': {
                'property': '比赛日期',
                'date': {'equals': date_str},
            },
            'page_size': 100,
        }
        if cursor: body['start_cursor'] = cursor

        d = notion_req('POST', 'data_sources/' + DS_ID + '/query', body)
        if not d: break

        all_pages.extend(d.get('results', []))
        if d.get('has_more'):
            cursor = d.get('next_cursor')
        else:
            break

    return all_pages


def match_notion_page(match_data, notion_pages):
    """从 Notion 页面列表中找到对应的比赛"""
    mn = match_data['match_num'].replace('周六', '').replace('周日', '')  # strip prefix if any
    home = match_data.get('home', '').strip()
    away = match_data.get('away', '').strip()

    for p in notion_pages:
        props = p.get('properties', {})
        title = ''.join(t['text']['content'] for t in props.get('Name', {}).get('title', []))
        # Try matching by match_num in title
        if mn in title:
            # Also try to match home/away if available
            if home and away:
                if home in title and away in title:
                    return p
            else:
                return p

    # Fallback: just match by match_num
    for p in notion_pages:
        props = p.get('properties', {})
        title = ''.join(t['text']['content'] for t in props.get('Name', {}).get('title', []))
        if mn in title:
            return p
    return None


def update_notion_remark(page_id, remark_text):
    """更新 Notion 页面的备注字段"""
    body = {
        'properties': {
            '备注': {
                'rich_text': [{'text': {'content': remark_text[:2000]}}]
            }
        }
    }
    d = notion_req('PATCH', 'pages/' + page_id, body)
    return d is not None


def main():
    print('=' * 60)
    print('模式匹配结果 → Notion 同步')
    print('=' * 60)

    # 1. 加载报告
    if not os.path.exists(REPORT_FILE):
        print('[1/3] 报告不存在，先跑 pattern_matcher.py')
        return
    report = json.loads(open(REPORT_FILE, 'r', encoding='utf-8').read())
    matches = report.get('matches', [])
    date_label = report.get('date', '')
    print('[1/3] 加载报告: %d场比赛命中模式 (%s)' % (len(matches), date_label))

    # 提取日期
    date_str = date_label.split(' ')[0] if ' ' in date_label else date_label

    # 2. 查询 Notion 页面
    print('[2/3] 查询 Notion 页面...')
    notion_pages = find_notion_pages_by_date(date_str)
    if not notion_pages:
        # Try without date filter - get all recent pages
        print('     日期 %s 无结果，尝试全量查询...' % date_str)
        for d in range(5):
            from datetime import timedelta
            test_date = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=d)).strftime('%Y-%m-%d') if date_str else ''
            if test_date:
                notion_pages = find_notion_pages_by_date(test_date)
                if notion_pages:
                    date_str = test_date
                    print('     改用日期 %s: %d页' % (date_str, len(notion_pages)))
                    break
        if not notion_pages:
            print('     Notion 无匹配页面，可能日期格式不匹配')
            return
    else:
        print('     找到 %d 个页面' % len(notion_pages))

    # 3. 逐条写入备注
    print('[3/3] 写入备注...')
    updated = 0
    not_found = 0
    for m in matches:
        page = match_notion_page(m, notion_pages)
        if not page:
            not_found += 1
            continue

        remark = format_remark(m)
        page_id = page['id']
        if update_notion_remark(page_id, remark):
            updated += 1
        else:
            print('  ❌ 更新失败: %s %s' % (m['match_num'], m.get('home', '')))

    print('')
    print('更新: %d场' % updated)
    print('未匹配: %d场' % not_found)
    print('✅ 完成!')


if __name__ == '__main__':
    main()
