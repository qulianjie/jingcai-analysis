# -*- coding: utf-8 -*-
"""
从 Notion 补全 feedback.json 的赛果数据
"""
import os, sys, json, urllib.request
from datetime import datetime, timedelta

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _util import ensure_utf8_stdout
    ensure_utf8_stdout()
except: pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
DS_ID = "35491ad7-17ba-81df-b58c-000ba04f22b7"
TOKEN = "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"


def notion_request(method, endpoint, body=None):
    url = 'https://api.notion.com/v1/' + endpoint
    headers = {
        'Authorization': 'Bearer ' + TOKEN,
        'Notion-Version': '2025-09-03',
        'Content-Type': 'application/json',
    }
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req).read().decode('utf-8')
        return json.loads(resp)
    except urllib.error.HTTPError as e:
        print('HTTP Error %d: %s' % (e.code, e.read().decode('utf-8')[:200]))
        return None


def query_notion_results(start_date, end_date):
    """查询 Notion 中有实际比分的比赛"""
    all_results = []
    cursor = None
    
    while True:
        body = {
            'filter': {
                'and': [
                    {'property': '实际比分', 'rich_text': {'is_not_empty': True}},
                    {'property': '比赛日期', 'date': {'on_or_after': start_date}},
                    {'property': '比赛日期', 'date': {'on_or_before': end_date}},
                ]
            },
            'sorts': [{'property': '比赛日期', 'direction': 'descending'}],
            'page_size': 100,
        }
        if cursor:
            body['start_cursor'] = cursor
        
        d = notion_request('POST', 'data_sources/' + DS_ID + '/query', body)
        if not d:
            break
        
        all_results.extend(d.get('results', []))
        
        if d.get('has_more'):
            cursor = d.get('next_cursor')
        else:
            break
    
    return all_results


def extract_rt(prop):
    """提取 rich_text 属性值"""
    if not prop: return ''
    rt = prop.get('rich_text', [])
    return ''.join(t['text']['content'] for t in rt)


def main():
    print('='*60)
    print('Notion赛果补全')
    print('='*60)
    
    # 读取现有feedback
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            fb = json.load(f)
    else:
        fb = {'dates': {}, 'stats': {'total_matches': 0, 'total_correct': 0, 'overall_accuracy': 0}}
    
    existing_dates = set(fb.get('dates', {}).keys())
    print('[1/3] 现有feedback日期: %d天, %d场' % (
        len(existing_dates),
        sum(len(v['feedback']) for v in fb.get('dates', {}).values())))
    
    # 查Notion 5月5号到现在的赛果
    today = datetime.now().strftime('%Y-%m-%d')
    print('[2/3] 查询Notion (2026-05-05 ~ %s)...' % today)
    notion_matches = query_notion_results('2026-05-05', today)
    print('     找到 %d 条含赛果的记录' % len(notion_matches))
    
    # 按日期+比赛编号分组
    added = 0
    skipped = 0
    dates_data = fb.get('dates', {})
    
    for r in notion_matches:
        props = r.get('properties', {})
        name = extract_rt(props.get('Name'))
        date = props.get('比赛日期', {}).get('date', {}).get('start', '')
        score = extract_rt(props.get('实际比分'))
        result = extract_rt(props.get('实际结果'))
        correct = props.get('预测正确', {}).get('checkbox', False)
        prediction = extract_rt(props.get('竞彩预测'))
        
        if not date or not score or not result:
            skipped += 1
            continue
        
        # 从name提取场次编号：如 "周六030 美职足 波特兰vs圣何塞" -> "030"
        match_num = ''
        import re
        m = re.match(r'(?:周[一二三四五六日])?(\d{3})', name)
        if m:
            match_num = m.group(1)
        
        if not match_num:
            skipped += 1
            continue
        
        # 如果该日期已在feedback中且有这场比赛，跳过
        date_fb = dates_data.get(date, {'feedback': []})
        existing_nums = set(f.get('match_num') for f in date_fb['feedback'])
        if match_num in existing_nums:
            continue
        
        # 信任度提取
        conf = ''
        if prediction:
            m = re.search(r'信心(\d+)%', prediction)
            if m: conf = m.group(1) + '%'
        
        # 添加反馈条目
        entry = {
            'match_num': match_num,
            'score': score,
            'predicted': '',
            'actual': result,
            'correct': correct,
            'confidence': conf or '',
        }
        
        if date not in dates_data:
            dates_data[date] = {'feedback': []}
        dates_data[date]['feedback'].append(entry)
        added += 1
    
    # 更新stats
    total = sum(len(v['feedback']) for v in dates_data.values())
    total_correct = sum(
        1 for v in dates_data.values()
        for f in v['feedback'] if f.get('correct')
    )
    
    fb['dates'] = dates_data
    fb['stats'] = {
        'total_matches': total,
        'total_correct': total_correct,
        'overall_accuracy': round(total_correct / total, 4) if total > 0 else 0,
    }
    
    # 保存
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)
    
    print('[3/3] 结果:')
    print('     新增 %d 场赛果' % added)
    print('     跳过 %d 条（无场次编号或已存在）' % skipped)
    print('     当前总场次: %d' % total)
    print('     当前总正确: %d (%.1f%%)' % (total_correct, total_correct/total*100 if total else 0))
    print('')
    
    print('新增的日期:')
    new_dates = [d for d in sorted(dates_data.keys()) if d not in existing_dates]
    for d in new_dates:
        cnt = len(dates_data[d]['feedback'])
        print('  %s: +%d场' % (d, cnt))
    
    print('\n✅ 完成!')


if __name__ == '__main__':
    main()
