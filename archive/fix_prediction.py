import os

fpath = r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_conclusion_generator.py'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the recommendation output line and add handicap prediction after it
old_line = "output.append(f'| **推荐** | {direction} |')"
new_lines = """output.append(f'| **推荐** | {direction} |')
output.append(f'| **让球预测** | {rq_direction}（信心{int(rq_confidence*100)}%） |')"""

if old_line in content:
    content = content.replace(old_line, new_lines)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - added handicap prediction line')
else:
    print('NOT FOUND: ' + old_line[:50])
