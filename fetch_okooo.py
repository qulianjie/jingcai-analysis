import requests
import re
import sys

url = 'https://m.okooo.com/kaijiang/sport.php?LotteryType=SportteryNWDL&LotteryNo=2026-05-10&from=/live/?LotteryType=jingca'

# 用GBK编码
r = requests.get(url, timeout=15)
r.encoding = 'gbk'
html = r.text

# 保存原始HTML
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\okooo_raw.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 提取所有比赛数据
# 格式: 编号 + 主队 + VS + 客队 + 比分(半场:全场) + 开奖
pattern = r'(\d{3})\s*\n?\s*(.*?)\s*VS\s*(.*?)\s*(\d+:\d+)\s*.*?(\d+:\d+)'
matches = re.findall(pattern, html, re.DOTALL)

print(f"找到 {len(matches)} 场比赛\n")

scores = {}
for m in matches:
    num = m[0].strip()
    home = m[1].strip().replace('\n', '').replace(' ', '')
    away = m[2].strip().replace('\n', '').replace(' ', '')
    ht_score = m[3].strip()
    ft_score = m[4].strip()
    
    # 竞彩编号格式
    day_num = f"周日{num}"
    scores[day_num] = ft_score
    
    print(f"{day_num}: {home} {ft_score} {away} (半场{ht_score})")

print(f"\n共提取 {len(scores)} 场比分")

# 保存为JSON
import json
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\data\okooo_scores_2026-05-10.json', 'w', encoding='utf-8') as f:
    json.dump(scores, f, ensure_ascii=False, indent=2)
print(f"\n已保存到 okooo_scores_2026-05-10.json")
