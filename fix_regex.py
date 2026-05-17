import re

f = open('jingcai/feedback.js', 'r', encoding='utf-8')
content = f.read()
f.close()

# 修复正则：[\u4E00-\u516D] 不匹配"四"，改为明确的枚举
old = r'[\u4E00-\u516D\u65E5]'
new = r'[\u4E00\u4E8C\u4E09\u56DB\u4E94\u516D\u65E5]'

count = content.count(old)
print(f'Found {count} occurrences')

content = content.replace(old, new)

f = open('jingcai/feedback.js', 'w', encoding='utf-8')
f.write(content)
f.close()

print('Fixed!')

# 验证
f = open('jingcai/feedback.js', 'r', encoding='utf-8')
lines = f.readlines()
f.close()
for i, line in enumerate(lines):
    if '4E00' in line or '4e00' in line:
        print(f'Line {i+1}: {line.rstrip()}')
