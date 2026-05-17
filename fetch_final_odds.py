# -*- coding: utf-8 -*-
"""从500.com实时获取终盘欧赔，更新到Notion（05-07到05-11）
直接用requests抓取，不调用subprocess
"""
import sys, os, re, json, time
import requests
from bs4 import BeautifulSoup

NOTION_API_KEY = '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'
DATABASE_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})

def notion_request(method, endpoint, data=None):
    import http.client
    conn = http.client.HTTPSConnection('api.notion.com')
    headers = {
        'Authorization': f'Bearer {NOTION_API_KEY}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode('utf-8') if data else None
    conn.request(method, endpoint, body, headers)
    res = conn.getresponse()
    d = res.read().decode('utf-8')
    try:
        return {'status': res.status, 'data': json.loads(d)}
    except:
        return {'status': res.status, 'data': d}

def query_by_date(date_str):
    data = {
        'filter': {'property': '比赛日期', 'date': {'equals': date_str}},
        'page_size': 100,
    }
    res = notion_request('POST', f'/v1/databases/{DATABASE_ID}/query', data)
    return res.get('data', {}).get('results', [])

def fetch_odds(fid):
    """从500.com抓取欧赔数据（同step146_extractor.py逻辑）"""
    try:
        r = sess.get(f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml', timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        all_companies = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12:
                    continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                nums = []
                for idx in [3, 4, 5, 6, 7, 8]:
                    val = tds[idx].get_text().strip().replace('\xa0', '')
                    try:
                        nums.append(float(val))
                    except:
                        pass
                if len(nums) >= 6:
                    if td0.isdigit():
                        all_companies.append({'row_num': int(td0), 'name': td1,
                            'lw': nums[3], 'ld': nums[4], 'll': nums[5]})
                    elif '平均值' in td1:
                        all_companies.append({'row_num': 99, 'name': '百家平均',
                            'lw': nums[3], 'ld': nums[4], 'll': nums[5]})
        
        odds = {}
        for c in all_companies:
            if c['row_num'] == 1:
                odds['jc'] = {
                    'win': round(c['lw'], 1),
                    'draw': round(c['ld'], 1),
                    'loss': round(c['ll'], 1),
                }
            elif c['row_num'] == 6:
                odds['iw'] = {
                    'win': round(c['lw'], 1),
                    'draw': round(c['ld'], 1),
                    'loss': round(c['ll'], 1),
                }
            elif c['row_num'] == 99:
                odds['bj'] = {
                    'win': round(c['lw'], 1),
                    'draw': round(c['ld'], 1),
                    'loss': round(c['ll'], 1),
                }
        
        return odds
    except Exception as e:
        return {}

def update_odds(page_id, odds):
    props = {}
    if odds.get('jc'):
        props['终盘竞彩欧赔胜'] = {'number': odds['jc']['win']}
        props['终盘竞彩欧赔平'] = {'number': odds['jc']['draw']}
        props['终盘竞彩欧赔负'] = {'number': odds['jc']['loss']}
    if odds.get('bj'):
        props['终盘百家欧赔胜'] = {'number': odds['bj']['win']}
        props['终盘百家欧赔平'] = {'number': odds['bj']['draw']}
        props['终盘百家欧赔负'] = {'number': odds['bj']['loss']}
    if odds.get('iw'):
        props['终盘Interwetten胜'] = {'number': odds['iw']['win']}
        props['终盘Interwetten平'] = {'number': odds['iw']['draw']}
        props['终盘Interwetten负'] = {'number': odds['iw']['loss']}
    
    if not props:
        return False
    
    res = notion_request('PATCH', f'/v1/pages/{page_id}', {'properties': props})
    return res['status'] == 200

def main():
    dates = ['2026-05-07', '2026-05-08', '2026-05-09', '2026-05-10', '2026-05-11']
    total_updated = 0
    total_failed = 0
    
    for date_str in dates:
        print(f'\n=== {date_str} ===')
        notion_records = query_by_date(date_str)
        print(f'Notion记录数: {len(notion_records)}')
        
        task_dir = os.path.join(TASKS_DIR, date_str)
        if not os.path.exists(task_dir):
            print(f'  本地目录不存在，跳过')
            continue
        
        report_files = [f for f in os.listdir(task_dir) if f.endswith('.md')]
        fid_map = {}
        for rf in report_files:
            content = open(os.path.join(task_dir, rf), 'r', encoding='utf-8').read()
            fid_match = re.search(r'FID[::]\s*(\d+)', content)
            num_match = re.search(r'周[一二三四五六日](\d{3})', rf)
            if fid_match and num_match:
                fid_map[num_match.group(1)] = fid_match.group(1)
        
        for record in notion_records:
            page_id = record['id']
            notion_name = record.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
            num_match = re.search(r'(\d{3})', notion_name)
            num = num_match.group(1) if num_match else ''
            
            if not num or num not in fid_map:
                print(f'  [SKIP] {notion_name} (无FID)')
                continue
            
            fid = fid_map[num]
            odds = fetch_odds(fid)
            
            if odds:
                success = update_odds(page_id, odds)
                if success:
                    jc = odds.get('jc', {})
                    bj = odds.get('bj', {})
                    iw = odds.get('iw', {})
                    jc_s = f"{jc.get('win')}/{jc.get('draw')}/{jc.get('loss')}" if jc else '-'
                    bj_s = f"{bj.get('win')}/{bj.get('draw')}/{bj.get('loss')}" if bj else '-'
                    iw_s = f"{iw.get('win')}/{iw.get('draw')}/{iw.get('loss')}" if iw else '-'
                    print(f'  [OK] {notion_name} 竞彩:{jc_s} 百家:{bj_s} IW:{iw_s}')
                    total_updated += 1
                else:
                    print(f'  [FAIL] {notion_name}')
                    total_failed += 1
            else:
                print(f'  [SKIP] {notion_name} 未获取到')
                total_failed += 1
            
            time.sleep(0.5)
    
    print(f'\n=== 完成 ===')
    print(f'成功: {total_updated} 失败: {total_failed}')

if __name__ == '__main__':
    main()
