# -*- coding: utf-8 -*-
"""Debug IW same odds calculation"""
import os, re

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in os.listdir(d):
    if f.startswith('match1_'):
        md = os.path.join(d, f)
        s3_path = os.path.join(md, 'group01_europe', 'step3_interwetten_same.txt')
        with open(s3_path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        
        # Extract current league
        league_match = re.search(r'当前联赛：\s*(.+)', text)
        current_league = league_match.group(1).strip() if league_match else ''
        print('Current league: %s' % current_league)
        
        # Count table rows
        rows = []
        for line in text.split('\n'):
            if '|' not in line or '---' in line or '赛事' in line:
                continue
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) < 8:
                continue
            
            result = cells[3] if len(cells) > 3 else ''
            if result not in ['胜', '平', '负']:
                continue
            
            panlu = cells[7] if len(cells) > 7 else '低'
            league = cells[8] if len(cells) > 8 else ''
            
            rows.append({
                'result': result,
                'panlu': panlu,
                'league': league.strip(),
                'is_same_league': current_league and league.strip() == current_league
            })
        
        print('Total rows: %d' % len(rows))
        
        # Count results
        wins = sum(1 for r in rows if r['result'] == '胜')
        draws = sum(1 for r in rows if r['result'] == '平')
        losses = sum(1 for r in rows if r['result'] == '负')
        print('Results: 胜%d 平%d 负%d' % (wins, draws, losses))
        print('Win rate: %.1f%%' % (wins / len(rows) * 100 if rows else 0))
        
        # Same league count
        same_league = sum(1 for r in rows if r['is_same_league'])
        print('Same league: %d' % same_league)
        
        # Panlu distribution
        high = sum(1 for r in rows if r['panlu'] == '高')
        mid = sum(1 for r in rows if r['panlu'] == '中')
        low = sum(1 for r in rows if r['panlu'] == '低')
        print('Panlu: 高%d 中%d 低%d' % (high, mid, low))
        
        # Calculate weighted score
        tier_weights = {
            ('高', True): 3.0,
            ('高', False): 2.0,
            ('中', True): 1.5,
            ('中', False): 1.0,
            ('低', True): 0.75,
            ('低', False): 0.5,
        }
        
        weighted_home = 0
        weighted_draw = 0
        weighted_away = 0
        total_weight = 0
        
        for row in rows:
            weight = tier_weights.get((row['panlu'], row['is_same_league']), 0.5)
            total_weight += weight
            
            if row['result'] == '胜':
                weighted_home += weight
            elif row['result'] == '平':
                weighted_draw += weight
            elif row['result'] == '负':
                weighted_away += weight
        
        print('\nWeighted: home=%.2f draw=%.2f away=%.2f total=%.2f' % (weighted_home, weighted_draw, weighted_away, total_weight))
        
        if total_weight > 0:
            weighted_win_rate = weighted_home / total_weight * 100
            score = (weighted_win_rate - 50) / 50
            print('Weighted win rate: %.1f%%' % weighted_win_rate)
            print('Score: %.3f' % score)
        
        break
