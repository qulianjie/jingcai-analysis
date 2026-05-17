import json
d=json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\learned_patterns_v2.json', encoding='utf-8'))
print('=== 高准确率组合 (TOP30) ===')
for c in d.get('high_accuracy_combos',[])[:30]:
    tag = c.get('tag','')
    acc = c['accuracy']
    cor = c['correct']
    tot = c['total']
    print(f'  {tag}: {acc:.0%} ({cor}/{tot})')
print()
print('=== 低准确率组合 (TOP20) ===')
for c in d.get('low_accuracy_combos',[])[:20]:
    tag = c.get('tag','')
    acc = c['accuracy']
    cor = c['correct']
    tot = c['total']
    print(f'  {tag}: {acc:.0%} ({cor}/{tot})')

# 提取所有唯一标签
all_tags = set()
for c in d.get('high_accuracy_combos',[]) + d.get('low_accuracy_combos',[]):
    tag = c.get('tag','')
    for part in tag.split('\u00d7'):  # ×
        all_tags.add(part.strip())
print()
print(f'=== 所有唯一标签 ({len(all_tags)}个) ===')
for t in sorted(all_tags):
    print(f'  {t}')
