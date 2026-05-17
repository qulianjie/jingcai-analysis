# -*- coding: utf-8 -*-
"""详细展示IW同赔分值计算过程"""
import os, re

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in os.listdir(d):
    if f.startswith('match1_'):
        md = os.path.join(d, f)
        s3_path = os.path.join(md, 'group01_europe', 'step3_interwetten_same.txt')
        with open(s3_path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        
        league_match = re.search(r'当前联赛：\s*(.+)', text)
        current_league = league_match.group(1).strip() if league_match else ''
        
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
        
        tier_weights = {
            ('高', True): 3.0,
            ('高', False): 2.0,
            ('中', True): 1.5,
            ('中', False): 1.0,
            ('低', True): 0.75,
            ('低', False): 0.5,
        }
        
        print('=== IW同赔分值计算 ===')
        print('')
        print('原始数据: %d场 (胜%d 平%d 负%d)' % (
            len(rows),
            sum(1 for r in rows if r['result'] == '胜'),
            sum(1 for r in rows if r['result'] == '平'),
            sum(1 for r in rows if r['result'] == '负'),
        ))
        print('原始胜率: %.1f%%' % (sum(1 for r in rows if r['result'] == '胜') / len(rows) * 100))
        print('')
        print('关键问题: 当前联赛=%s, 同联赛场数=%d (全部为False)' % (
            current_league,
            sum(1 for r in rows if r['is_same_league'])
        ))
        print('')
        print('盘路分布:')
        for panlu in ['高', '中', '低']:
            count = sum(1 for r in rows if r['panlu'] == panlu)
            win = sum(1 for r in rows if r['panlu'] == panlu and r['result'] == '胜')
            print('  %s: %d场 (其中胜%d场, 权重=%.2f)' % (panlu, count, win, tier_weights[(panlu, False)]))
        print('')
        
        # Show weighted calculation
        weighted_home = 0
        weighted_draw = 0
        weighted_away = 0
        total_weight = 0
        
        print('加权计算:')
        for row in rows:
            weight = tier_weights.get((row['panlu'], row['is_same_league']), 0.5)
            total_weight += weight
            
            if row['result'] == '胜':
                weighted_home += weight
                label = '胜(%.2f)' % weight
            elif row['result'] == '平':
                weighted_draw += weight
                label = '平(%.2f)' % weight
            elif row['result'] == '负':
                weighted_away += weight
                label = '负(%.2f)' % weight
            print('  %s: %s' % (row['panlu'], label))
        
        print('')
        print('加权结果:')
        print('  胜加权: %.2f' % weighted_home)
        print('  平加权: %.2f' % weighted_draw)
        print('  负加权: %.2f' % weighted_away)
        print('  总加权: %.2f' % total_weight)
        print('')
        
        if total_weight > 0:
            weighted_win_rate = weighted_home / total_weight * 100
            score = (weighted_win_rate - 50) / 50
            print('加权胜率: %.1f%%' % weighted_win_rate)
            print('分值公式: (加权胜率 - 50) / 50')
            print('分值: (%.1f - 50) / 50 = %.3f' % (weighted_win_rate, score))
            print('')
            print('结论: IW同赔 = %.3f 中立' % score)
        
        break
