import os, re
from bs4 import BeautifulSoup

data_dir = 'jingcai/tasks/2026-05-12/data/match1_仁川联__浦项制铁/group03_asian'
html_file = os.path.join(data_dir, 'raw_asian.html')
if not os.path.exists(html_file):
    # 检查meta中是否有meta.json
    meta_path = 'jingcai/tasks/2026-05-12/data/match1_仁川联__浦项制铁/meta.json'
    # 直接读step6看看内容
    s6 = os.path.join(data_dir, 'step6_asian_base.txt')
    if os.path.exists(s6):
        print('=== step6 content ===')
        print(open(s6, encoding='utf-8').read())
    else:
        print('no step6 file')
else:
    html = open(html_file, encoding='utf-8').read()
    soup = BeautifulSoup(html, 'html.parser')
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
        
        print('=== Table with Asian handicap data ===')
        for i, tr in enumerate(trs[:4]):
            tds = tr.find_all('td')
            if not tds:
                continue
            print('Row %d (%d tds):' % (i, len(tds)))
            for j, td in enumerate(tds):
                val = td.get_text().strip().replace('\xa0', ' ')
                if val:
                    print('  td[%d] = "%s"' % (j, val))
            print()
        break
