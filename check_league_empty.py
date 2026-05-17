import requests, re

url = 'https://trade.500.com/jczq/?playid=269&g=2&date=2026-05-11'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers, timeout=15)
html = r.content.decode('gbk', errors='ignore')

# Find all tr blocks with data-fixtureid
tr_pattern = r'<tr[^>]*data-fixtureid="([^"]*)"[^>]*>'
matches = list(re.finditer(tr_pattern, html))

print(f'Total matches: {len(matches)}')
empty_league_count = 0

for m in matches:
    fid = m.group(1)
    # Get the full tr tag
    tr_start = m.start()
    tr_end = html.find('</tr>', tr_start)
    tr_block = html[tr_start:tr_end] if tr_end > 0 else tr_block
    
    league_match = re.search(r'data-simpleleague="([^"]*)"', tr_block)
    if league_match:
        league_val = league_match.group(1)
        if not league_val:
            empty_league_count += 1
            print(f'FID={fid}: league=EMPTY')
    else:
        empty_league_count += 1
        print(f'FID={fid}: league=MISSING')

print(f'\nEmpty/missing league count: {empty_league_count}/{len(matches)}')
