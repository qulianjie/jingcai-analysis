import json
import requests
import os
import re
import glob
import sys

# Fix encoding for Windows console
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
TASK_DIR = os.path.join(os.path.dirname(__file__), 'tasks', '2026-05-10')

# 从截图识别的30场比分（全部正确）
SCORES = {
    '周日001': '3:0', '周日002': '0:0', '周日003': '1:1', '周日004': '1:0',
    '周日005': '1:1', '周日006': '1:0', '周日007': '0:0', '周日008': '0:1',
    '周日009': '1:1', '周日010': '1:2', '周日011': '2:3', '周日012': '0:2',
    '周日013': '1:1', '周日014': '0:2', '周日015': '0:1', '周日016': '0:1',
    '周日017': '2:1', '周日018': '2:2', '周日019': '1:2', '周日020': '1:0',
    '周日021': '0:2', '周日022': '0:3', '周日023': '1:0', '周日024': '2:1',
    '周日025': '2:2', '周日026': '1:1', '周日027': '3:1', '周日028': '1:0',
    '周日029': '0:2', '周日030': '2:1',
}

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

def query_matches():
    data = json.dumps({
        'filter': {'and': [{'property': '比赛日期', 'date': {'equals': '2026-05-10'}}]},
        'page_size': 100
    })
    r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query',
                      headers=HEADERS, data=data)
    return r.json()['results']

def prediction_to_result(pred):
    if not pred: return None
    if '主胜' in pred: return '胜'
    if '客胜' in pred: return '负'
    if '平' in pred: return '平'
    return None

def get_handicap(match_num):
    files = glob.glob(os.path.join(TASK_DIR, f'{match_num}*.md'))
    if not files:
        return 0
    with open(files[0], 'r', encoding='utf-8') as f:
        content = f.read()
    rq_table = re.search(r'\|\s*竞彩官方\s*\|\s*([+-]?\d+(?:\.5)?)\s*\|', content)
    if rq_table:
        return -float(rq_table[1])
    return 0

def update_match(page_id, score, pred, rq_pred, handicap):
    hs, as_ = map(int, score.split(':'))
    adj_hs = hs - handicap
    
    if hs > as_: actual_result = '胜'
    elif hs < as_: actual_result = '负'
    else: actual_result = '平'
    
    pred_result = prediction_to_result(pred)
    is_correct = pred_result == actual_result if pred_result else None
    
    if adj_hs > as_: rq_actual = '胜'
    elif adj_hs < as_: rq_actual = '负'
    else: rq_actual = '平'
    
    rq_correct = None
    if rq_pred:
        rq_pred_result = prediction_to_result(rq_pred)
        rq_correct = rq_pred_result == rq_actual
    
    if handicap > 0: rq_text = f'让{handicap}球'
    elif handicap < 0: rq_text = f'受让{abs(handicap)}球'
    else: rq_text = '平手'
    
    summary = f'竞彩: {pred} -> {actual_result} ({score})'
    if rq_pred:
        summary += f'\n让球{rq_text}: {rq_pred} -> {rq_actual} ({adj_hs}:{as_})'
    
    props = {
        '实际比分': {'rich_text': [{'text': {'content': score}}]},
        '实际结果': {'rich_text': [{'text': {'content': actual_result}}]},
        '反馈日期': {'date': {'start': '2026-05-11'}},
        '反馈总结': {'rich_text': [{'text': {'content': summary}}]},
        '预测正确': {'checkbox': is_correct if is_correct is not None else False},
    }
    if rq_correct is not None:
        props['让球预测正确'] = {'checkbox': rq_correct}
    
    r = requests.patch(f'https://api.notion.com/v1/pages/{page_id}',
                       headers=HEADERS, data=json.dumps({'properties': props}))
    return is_correct, rq_correct

# Main
pages = query_matches()
print(f'Notion中找到 {len(pages)} 场比赛')

page_map = {}
for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    if m:
        page_map[m.group(1)] = p

print(f'映射到 {len(page_map)} 场')
print()

updated = 0
correct = 0
wrong = 0

for mn, score in sorted(SCORES.items()):
    page = page_map.get(mn)
    if not page:
        print(f'[X] {mn} - Notion中未找到')
        continue
    
    pred = page['properties']['竞彩预测']['rich_text'][0]['plain_text'] if page['properties']['竞彩预测']['rich_text'] else ''
    rq_pred = ''
    rq_prop = page['properties'].get('让球预测', {})
    if rq_prop.get('rich_text'):
        rq_pred = rq_prop['rich_text'][0].get('plain_text', '')
    
    handicap = get_handicap(mn)
    
    try:
        is_corr, rq_corr = update_match(page['id'], score, pred, rq_pred, handicap)
        
        hs, as_ = map(int, score.split(':'))
        adj_hs = hs - handicap
        if adj_hs > as_: rq_actual = '胜'
        elif adj_hs < as_: rq_actual = '负'
        else: rq_actual = '平'
        
        rq_status = ''
        if rq_pred:
            rq_ok = '[OK]' if rq_corr else '[X]'
            rq_status = f' | 让球:{rq_pred}->{rq_actual} {rq_ok}'
        
        actual_r = '胜' if hs>as_ else '负' if hs<as_ else '平'
        pred_ok = '[OK]' if is_corr else '[X]'
        print(f'{mn} {score} 竞彩:{pred}->{actual_r} {pred_ok}{rq_status}')
        updated += 1
        if is_corr: correct += 1
        else: wrong += 1
    except Exception as e:
        print(f'[X] {mn} 更新失败: {e}')

print()
print(f'=== 反馈完成 ===')
print(f'   已更新: {updated}')
print(f'   竞彩正确: {correct}/{updated}')
print(f'   竞彩错误: {wrong}/{updated}')
