# -*- coding: utf-8 -*-
"""
Check if 500.com pages have the needed data for a match
"""
import requests, re, sys
from bs4 import BeautifulSoup
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
})

FID = '1373089'

# Check yazhi page
print("=== Step 6: 亚盘页面 ===")
try:
    r = sess.get(f'https://odds.500.com/fenxi/yazhi-{FID}.shtml', timeout=15)
    r.encoding = 'gbk'
    print(f"Status: {r.status_code}, Size: {len(r.text)}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Find tables
    tables = soup.find_all('table')
    print(f"Tables found: {len(tables)}")
    
    # Look for 澳门 (Macau) row
    for table in tables:
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12: continue
            name = tds[1].get_text().strip()
            if '澳' in name or '门' in name:
                print(f"Found Macau row: {name}")
                for i, td in enumerate(tds):
                    val = td.get_text().strip().replace('\xa0', '')
                    print(f"  td[{i}] = {val[:50]}")
                break
    
    # Look for any Asian handicap data
    print("\nAll rows with >= 10 td:")
    for table in tables:
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 10: continue
            name = tds[1].get_text().strip()
            if name:
                print(f"  Row: {name}")
except Exception as e:
    print(f"Error: {e}")

# Check if we can find team IDs from ouzhi page
print("\n\n=== Step 1: 欧赔页面（找球队ID）===")
try:
    r2 = sess.get(f'https://odds.500.com/fenxi/ouzhi-{FID}.shtml', timeout=15)
    r2.encoding = 'gbk'
    print(f"Status: {r2.status_code}, Size: {len(r2.text)}")
    
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    # Find team links
    team_links = []
    for a in soup2.find_all('a', href=True):
        href = a.get('href', '')
        tm = re.search(r'/team/(\d+)/', href)
        if tm:
            atxt = a.get_text().strip()
            if atxt and len(atxt) > 1:
                team_links.append((tm.group(1), atxt))
    
    print(f"Team links found: {team_links}")
    
    # Also check for team names
    print("\nTeam names on page:")
    for span in soup2.find_all('span'):
        txt = span.get_text().strip()
        if 'vs' in txt.lower() or '全北' in txt or '光州' in txt:
            print(f"  {txt[:100]}")
except Exception as e:
    print(f"Error: {e}")

# Check team fixture page
print("\n\n=== Team fixture page ===")
try:
    r3 = sess.get('https://liansai.500.com/team/1609/teamfixture/', timeout=15)
    r3.encoding = 'gbk'
    soup3 = BeautifulSoup(r3.text, 'html.parser')
    for tr in soup3.find_all('tr', attrs={'data': True}):
        data = tr.get('data', '')
        if '全北' in data or '光州' in data:
            print(f"Match data: {data[:200]}")
            break
    # Check league IDs
    for a in soup3.find_all('a', href=True):
        href = a.get('href', '')
        m = re.search(r'/zuqiu-(\d+)/', href)
        if m:
            print(f"League ID: {m.group(1)} in {href}")
            break
except Exception as e:
    print(f"Error: {e}")
