# -*- coding: utf-8 -*-
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
fp = os.path.join(SCRIPT_DIR, 'batch_feedback.py')

with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add 让球预测 extraction after pred = '胜/负', before # Extract confidence
old1 = "    pred = '胜/负'\n    \n    # Extract confidence"
new1 = """    pred = '胜/负'
    
    # Extract 让球预测
    rq_pred = ''
    rq_conf = ''
    rq_match = re.search(r'\\*\\*让球预测\\*\\*\\s*\\|\\s*([^\\|]+)', content)
    if rq_match:
        rq_text = rq_match.group(1).strip()
        if '让球胜' in rq_text:
            rq_pred = '胜'
        elif '让球平' in rq_text:
            rq_pred = '平'
        elif '让球负' in rq_text:
            rq_pred = '负'
        rq_conf_match = re.search(r'\\((\d+)%\\)', rq_text)
        if rq_conf_match:
            rq_conf = rq_conf_match.group(1) + '%'
    
    # Extract confidence"""

if old1 in content:
    content = content.replace(old1, new1, 1)
    print('Step 1: Added 让球预测 extraction')
else:
    print('Step 1: NOT FOUND (may already be patched)')

# 2. Add rq_pred and rq_conf to the return dict
old2 = "        'predicted': pred,\n        'confidence': confidence,\n        'league': league,"
new2 = "        'predicted': pred,\n        'confidence': confidence,\n        'rq_pred': rq_pred,\n        'rq_conf': rq_conf,\n        'league': league,"

if old2 in content:
    content = content.replace(old2, new2, 1)
    print('Step 2: Added rq_pred/rq_conf to return dict')
else:
    print('Step 2: NOT FOUND (may already be patched)')

# 3. Add rq_pred and rq_correct to feedback entry
old3 = "            'predicted': item['predicted'],\n            'actual': item['actual'],\n            'correct': item['correct'],\n            'confidence': item.get('confidence', ''),\n        }"
new3 = "            'predicted': item['predicted'],\n            'actual': item['actual'],\n            'correct': item['correct'],\n            'confidence': item.get('confidence', ''),\n            'rq_pred': item.get('rq_pred', ''),\n            'rq_correct': item.get('rq_correct', False),\n        }"

if old3 in content:
    content = content.replace(old3, new3, 1)
    print('Step 3: Added rq_pred/rq_correct to feedback entry')
else:
    print('Step 3: NOT FOUND (may already be patched)')

# 4. Add rq_correct computation in the comparison loop
old4 = "        is_correct = (predicted == actual) and actual != '待查'\n        if actual != '待查':\n            total_checked += 1\n            if is_correct:\n                total_correct += 1\n        \n        feedback_items.append({"
new4 = "        is_correct = (predicted == actual) and actual != '待查'\n        if actual != '待查':\n            total_checked += 1\n            if is_correct:\n                total_correct += 1\n        \n        # 让球预测正确性\n        rq_pred = pred_data.get('rq_pred', '')\n        rq_correct = (rq_pred == actual) and actual != '待查' and rq_pred != ''\n        \n        feedback_items.append({"

if old4 in content:
    content = content.replace(old4, new4, 1)
    print('Step 4: Added rq_correct computation')
else:
    print('Step 4: NOT FOUND (may already be patched)')

# 5. Add rq_pred and rq_correct to feedback_items.append
old5 = "            'predicted': predicted,\n            'actual': actual,\n            'correct': is_correct,\n            'confidence': confidence,\n            'league': league,\n        })"
new5 = "            'predicted': predicted,\n            'actual': actual,\n            'correct': is_correct,\n            'confidence': confidence,\n            'rq_pred': rq_pred,\n            'rq_correct': rq_correct,\n            'league': league,\n        })"

if old5 in content:
    content = content.replace(old5, new5, 1)
    print('Step 5: Added rq_pred/rq_correct to feedback_items')
else:
    print('Step 5: NOT FOUND (may already be patched)')

with open(fp, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')
