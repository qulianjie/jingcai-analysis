import sys, os, requests, re
from bs4 import BeautifulSoup

fid = sys.argv[1] if len(sys.argv) > 1 else '1373141'
url = 'https://odds.500.com.cn/fenxi/shuju-%s.shtml' % fid

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for table in soup.find_all('table'):
        trs = table.find_all('tr')
        if len(trs) < 3:
            continue
        has_num_rows = False
        for tr in trs:
            tds = tr.find_all('td')
            if tds and tds[0].get_text().strip().isdigit():
                has_num_rows = True
                break
        if not has_num_rows:
            continue
        
        print('=== Asian handicap table ===')
        for i, tr in enumerate(trs[:4]):
            tds = tr.find_all('td')
            if not tds:
                continue
            print('Row %d (%d tds):' % (i, len(tds)))
            for j, td in enumerate(tds):
                val = td.get_text().strip().replace('\xa0', ' ')
                colspan = td.get('colspan', '1')
                print('  td[%d](colspan=%s) = "%s"' % (j, colspan, val))
            print()
        break
except Exception as e:
    print('Error: %s' % e)
