# -*- coding: utf-8 -*-
"""构建完整训练数据集"""
import os, re, json
from collections import defaultdict

TASKS = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
FB_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json'
OUT_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\training_data.json'
DIM_NAMES = ['欧赔趋势','竞彩同赔','IW同赔','澳门亚盘','让球同赔','主队主场','客队客场','百家对比','盘路匹配','庄家盈亏']

def load_results():
    fb = json.load(open(FB_PATH,'r',encoding='utf-8'))
    results = {}
    for date_str, day_data in fb.get('dates',{}).items():
        if date_str == '--date': continue
        for rec in day_data.get('feedback',[]):
            mn = rec.get('match_num','').strip()
            actual = rec.get('actual','')
            if mn and actual in ('胜','平','负'):
                results[(date_str, mn)] = rec
    return results

def parse_report(fp):
    with open(fp,'r',encoding='utf-8') as f: text = f.read()
    # 从文件名取match_num (后3位数字)
    m = re.search(r'(\d{3})', os.path.basename(fp))
    mn = m.group(1) if m else ''
    # 竞彩预测
    pred = (re.search(r'\*\*竞彩预测\*\*\s*\|?\s*([^\n|]+)', text) or re.search(r'竞彩预测[：:]\s*([^\n]+)', text))
    pred = pred.group(1).strip() if pred else ''
    # 综合分值
    score = (re.search(r'\*\*综合分值\*\*\s*\|?\s*([+-]\d+\.\d+)', text) or re.search(r'综合分值[：:]\s*([+-]\d+\.\d+)', text))
    score = score.group(1) if score else ''
    # 信心
    conf = (re.search(r'\*\*信心\*\*\s*\|?\s*(\d+%)', text) or re.search(r'信心[：:]\s*(\d+%)', text))
    conf = conf.group(1) if conf else ''
    # 维度信号表
    dim_scores = {}
    block = re.search(r'### 各维度信号明细.*?\n\| 维度.*?\n\|[-\|]+.*?\n((?:\|.*?\n)+)', text, re.DOTALL)
    if block:
        for line in block.group(1).strip().split('\n'):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) >= 3:
                sm = re.search(r'([+-]?\d+\.\d+)', cells[1])
                if sm and cells[0] in DIM_NAMES:
                    dim_scores[cells[0]] = float(sm.group(1))
    return {'match_num': mn, 'prediction': pred, 'composite_score': score, 'confidence': conf, 'dim_scores': dim_scores}

def parse_match_dir(match_dir, mn):
    data = {}
    if not match_dir or not os.path.isdir(match_dir): return data
    # step25
    s25 = os.path.join(match_dir, 'step25_zhuangjia.json')
    if os.path.exists(s25):
        with open(s25,'r',encoding='utf-8') as f:
            d = json.load(f)
        ds = d.get('data',{})
        data['step25'] = {
            'bet_pct': {k: v.get('bet_pct','') for k,v in ds.items()},
            'profit_raw': {k: v.get('profit_raw','') for k,v in ds.items()},
            'profit': {k: v.get('profit','') for k,v in ds.items()},
        }
    # cache
    cache = os.path.join(match_dir, 'fid_odds_cache.json')
    if os.path.exists(cache):
        with open(cache,'r',encoding='utf-8') as f:
            c = json.load(f)
        meta = os.path.join(match_dir, 'meta.json')
        if os.path.exists(meta):
            with open(meta,'r',encoding='utf-8') as f:
                m = json.load(f)
            fid = str(m.get('fid',''))
            md = c.get(fid, {})
            data['cache'] = {'jc': md.get('jc',{}), 'iw': md.get('iw',{}), 'av': md.get('av',{})}
    return data

def find_match_dir(td, mn):
    data_dir = os.path.join(td, 'data')
    if not os.path.isdir(data_dir): return None
    for m in os.listdir(data_dir):
        mp = os.path.join(data_dir, m)
        if not os.path.isdir(mp): continue
        meta_path = os.path.join(mp, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path,'r',encoding='utf-8') as f:
                meta = json.load(f)
            if meta.get('matchnum','') == mn:
                return mp
    return None

def main():
    results = load_results()
    dates = sorted(os.listdir(TASKS))
    samples = []
    no_result = 0
    parsed = 0
    dim_total = defaultdict(int)
    
    for d in dates:
        td = os.path.join(TASKS, d)
        if not os.path.isdir(td): continue
        for f in sorted(os.listdir(td)):
            if not f.endswith('.md'): continue
            if f in ['sunday_matches.md','monday_matches.md','season_schedule.md']: continue
            
            report = parse_report(os.path.join(td, f))
            mn = report['match_num']
            
            # 匹配赛果（尝试多种格式）
            rec = results.get((d, mn)) or results.get((d, str(int(mn)))) if mn else None
            if not rec:
                no_result += 1
                continue
            actual = rec.get('actual','')
            if actual not in ('胜','平','负'): continue
            if not report['dim_scores']:
                continue
            
            parsed += 1
            for dim in report['dim_scores']:
                dim_total[dim] += 1
            
            sample = {
                'date': d, 'match_num': mn, 'match': f.replace('.md',''),
                'actual': actual, 'dim_scores': report['dim_scores'],
            }
            if report['prediction']: sample['prediction'] = report['prediction']
            if report['composite_score']: sample['composite_score'] = float(report['composite_score'])
            if report['confidence']: sample['confidence'] = report['confidence']
            
            md = find_match_dir(td, mn)
            if md:
                extra = parse_match_dir(md, mn)
                sample.update(extra)
            
            samples.append(sample)
    
    print(f'总报告数: {parsed+no_result}')
    print(f'匹配到赛果: {parsed}')
    print(f'无赛果: {no_result}')
    print(f'\n维度覆盖率(共{parsed}条):')
    for dim in DIM_NAMES:
        pct = dim_total.get(dim,0)/parsed*100 if parsed > 0 else 0
        print(f'  {dim}: {dim_total.get(dim,0):>4d}/{parsed} ({pct:4.0f}%)')
    
    # 统计赛果分布
    actual_dist = defaultdict(int)
    for s in samples:
        actual_dist[s['actual']] += 1
    print(f'\n赛果分布:')
    for k in ['胜','平','负']:
        print(f'  {k}: {actual_dist.get(k,0)} ({actual_dist.get(k,0)/len(samples)*100:.1f}%)')
    
    with open(OUT_PATH,'w',encoding='utf-8') as f:
        json.dump({'version':2,'total':len(samples),'samples':samples}, f, ensure_ascii=False, indent=2)
    print(f'\n✅ 已保存: {OUT_PATH}')

if __name__ == '__main__':
    main()
