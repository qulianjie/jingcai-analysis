# -*- coding: utf-8 -*-
"""Add rq_pred/rq_correct to feedback_items.append in batch_feedback.py"""
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
fp = os.path.join(SCRIPT_DIR, 'batch_feedback.py')

with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        feedback_items.append({
            'match_num': match_num,
            'match_name': '{} vs {}'.format(
                result_data.get('home', pred_data.get('home', '')),
                result_data.get('away', pred_data.get('away', ''))
            ),
            'score': result_data.get('score', ''),
            'actual': actual,
            'predicted': predicted,
            'confidence': confidence,
            'correct': is_correct,
            'league': pred_data.get('league', ''),
            'combo_features': pred_data.get('combo_features', {}),
        })"""

new = """        feedback_items.append({
            'match_num': match_num,
            'match_name': '{} vs {}'.format(
                result_data.get('home', pred_data.get('home', '')),
                result_data.get('away', pred_data.get('away', ''))
            ),
            'score': result_data.get('score', ''),
            'actual': actual,
            'predicted': predicted,
            'confidence': confidence,
            'correct': is_correct,
            'rq_pred': rq_pred,
            'rq_correct': rq_correct,
            'league': pred_data.get('league', ''),
            'combo_features': pred_data.get('combo_features', {}),
        })"""

if old in content:
    content = content.replace(old, new, 1)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - added rq_pred/rq_correct to feedback_items.append')
else:
    print('NOT FOUND')
