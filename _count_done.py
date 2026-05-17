"""实时检查比赛完成状态"""
import os, json

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-17\data'
matches_json = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-17\matches_data.json'

if not os.path.exists(d):
    print('0/0')
    exit()

# 读取比赛列表
with open(matches_json, 'r', encoding='utf-8') as f:
    data = json.load(f)
if 'groups' in data:
    for g in data['groups']:
        if 'matches' in data['groups'][g]:
            all_matches = data['groups'][g]['matches']
            break
elif 'matches' in data:
    all_matches = data['matches']
else:
    all_matches = data

# 检查 step24 完成情况
done = 0
total = len(all_matches)
for i, m in enumerate(all_matches):
    mn = str(m.get('matchnum', str(i+1)))
    fid = str(m.get('fid', ''))
    found = False
    for dirname in os.listdir(d):
        if dirname.startswith('match'):
            fp = os.path.join(d, dirname, 'step24_panlu_match.json')
            if os.path.exists(fp) and os.path.getsize(fp) > 100:
                mp = os.path.join(d, dirname, 'meta.json')
                if os.path.exists(mp):
                    with open(mp, 'r', encoding='utf-8') as mf:
                        mm = json.load(mf)
                    if mm.get('matchnum') == mn or mm.get('fid') == fid:
                        found = True
                        break
    if found:
        done += 1

print(f'{done}/{total}')
