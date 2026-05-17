import os, sys
sys.stdout = open(1, 'w', encoding='utf-8', errors='replace', closefd=False)

rd = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-17'

for num in range(19, 35):
    mn = '周日{:03d}'.format(num)
    fname = None
    for f in sorted(os.listdir(rd)):
        if f.startswith(mn.replace(' ', '_')) and f.endswith('.md') and f != 'sunday_matches.md':
            fname = f
            break
    if not fname: 
        print('未找到 {} 的报告文件'.format(mn))
        continue
    
    fp = os.path.join(rd, fname)
    with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    
    # 从文件名获取对阵
    parts = fname.replace('.md', '').split('_', 1)
    match_name = '{} {}'.format(parts[0], parts[1]) if len(parts) > 1 else parts[0]
    
    # 找第九节末尾的综合结论表格
    ninth_idx = content.find('# 第九步')
    if ninth_idx < 0: ninth_idx = content.find('第九步')
    if ninth_idx < 0: ninth_idx = max(content.find('# 第九'), content.find('## 第九'))
    
    pred = ''; rq = ''; conf = ''; score_val = ''
    best_fav = ''; profit = ''
    
    if ninth_idx >= 0:
        section = content[ninth_idx:]
        for line in section.split('\n'):
            cl = line.strip()
            # 庄家最看好在综合结论部分
            if '庄家最看好' in cl:
                # 文本格式: **庄家最看好**: 客胜 或 | **庄家最看好** | 客胜 |
                cc = cl.replace('**', '').strip('|').strip()
                if '：' in cc: best_fav = cc.split('：')[1].strip()
                elif '|' in cl and '庄家最看好' in cl:
                    bp = [x.strip() for x in cl.split('|') if x.strip()]
                    for i, x in enumerate(bp):
                        if '庄家最看好' in x and i+1 < len(bp):
                            best_fav = bp[i+1].replace('**', '').strip()
            elif '庄家盈亏' in cl:
                cc = cl.replace('**', '').strip('|').strip()
                if '庄家盈亏' in cc:
                    cc2 = cc.split('：')
                    if len(cc2) > 1: profit = cc2[1].strip()
                    else: profit = cc
    else:
        # 全局找
        for line in content.split('\n'):
            cl = line.strip().replace('**', '')
            if '庄家最看好' in cl and '：' in cl:
                best_fav = cl.split('：')[1].strip()
                break
    
    # 找第九节的表格行
    if ninth_idx >= 0:
        for line in content[ninth_idx:].split('\n'):
            cl = line.strip().replace('**', '').strip('|').strip()
            if cl.startswith('竞彩预测') or '竞彩预测' in line.split('|')[0] if '|' in line else False:
                bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
                if len(bp) >= 2:
                    pred = bp[1]
            if '让球预测' in (line.split('|')[0] if '|' in line else ''):
                bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
                if len(bp) >= 2:
                    rq = bp[1]
    
    # 另外全局找竞彩预测/让球预测（避开表格）
    if not pred:
        for line in content.split('\n'):
            cl = line.strip().replace('**', '').strip('|').strip()
            if cl.startswith('竞彩预测') or ( '竞彩预测' in cl and len(cl) < 80):
                bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
                if len(bp) >= 2: pred = bp[1]; break
    
    if not rq:
        for line in content.split('\n'):
            cl = line.strip().replace('**', '').strip('|').strip()
            if cl.startswith('让球预测') or ('让球预测' in cl and len(cl) < 120):
                bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
                if len(bp) >= 2: rq = bp[1]; break
    
    # 信心
    for line in content[ninth_idx:].split('\n') if ninth_idx >= 0 else content.split('\n'):
        cl = line.strip().replace('**', '').strip('|').strip()
        if cl.startswith('信心') or cl.startswith('信心等级'):
            bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
            if len(bp) >= 2: conf = bp[1]; break
    
    # 综合分值那行
    for line in content[ninth_idx:].split('\n') if ninth_idx >= 0 else content.split('\n'):
        if '综合分值' in line or '综合评分' in line or '综合值' in line:
            bp = [x.strip().replace('**','').strip() for x in line.split('|') if x.strip()]
            if len(bp) >= 2:
                score_val = bp[1]; break
    
    print('--- {} ---'.format(match_name))
    print('  竞彩预测: {}'.format(pred if pred else '(未提取到)'))
    print('  让球预测: {}'.format(rq if rq else '(未提取到)'))
    print('  庄家最看好: {}'.format(best_fav if best_fav else '(未提取到)'))
    if score_val: print('  综合分值: {}'.format(score_val))
    if conf: print('  信心: {}'.format(conf))
    if profit: print('  庄家盈亏: {}'.format(profit))
    
    # 欧赔趋势
    for line in content.split('\n'):
        cl = line.strip().replace('**', '')
        if '欧赔趋势' in cl or '欧赔方向' in cl:
            bp = [x.strip() for x in line.split('|') if x.strip()]
            if len(bp) >= 2: print('  欧赔方向: {}'.format(bp[1].replace('**', '').strip()))
            break
    
    print()
