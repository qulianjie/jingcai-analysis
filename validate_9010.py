# -*- coding: utf-8 -*-
"""90/10交叉验证：数据驱动 vs 手拍"""
import json, math, random
from collections import defaultdict

DATA_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\training_data.json'
DIM_ZH = ['欧赔趋势','竞彩同赔','IW同赔','澳门亚盘','让球同赔','主队主场','客队客场','百家对比','盘路匹配','庄家盈亏']

def load_data():
    data = json.load(open(DATA_PATH,'r',encoding='utf-8'))
    return data['samples']

def learn_weights(samples):
    weights = {}
    for dim_zh in DIM_ZH:
        pairs = [(s['dim_scores'].get(dim_zh,0), s['actual']) for s in samples]
        pairs = [(s,a) for s,a in pairs if abs(s) > 0.01]
        n = len(pairs)
        if n < 10:
            weights[dim_zh] = 1.0 / len(DIM_ZH)
            continue
        base_home = sum(1 for _,a in pairs if a=='胜') / n
        pos = [(s,a) for s,a in pairs if s > 0.1]
        neg = [(s,a) for s,a in pairs if s < -0.1]
        pos_acc = sum(1 for _,a in pos if a=='胜') / len(pos) if pos else base_home
        neg_acc = sum(1 for _,a in neg if a=='负') / len(neg) if neg else base_home
        lift = max(pos_acc/max(base_home,0.01), neg_acc/max(base_home,0.01))
        w = max(0.5, min(2.0, lift))
        weights[dim_zh] = w
    tw = sum(weights.values())
    if tw > 0:
        for k in weights: weights[k] /= tw
    return weights

def learn_thresholds(samples, weights):
    ws = []
    for s in samples:
        ts=0; tw=0
        for dim_zh, w in weights.items():
            sc = s['dim_scores'].get(dim_zh, 0)
            if abs(sc) > 0.01: ts += sc*w; tw += w
        if tw > 0: ws.append((ts/tw, s['actual']))
    th = {}
    for tgt in ('胜','平','负'):
        best = {'th':0,'p':0,'r':0,'f1':0}
        for tc in [i/100 for i in range(-50,51,3)]:
            pp = [(s,a) for s,a in ws if (tgt=='胜' and s>tc) or (tgt=='负' and s<-tc) or (tgt=='平' and abs(s)<abs(tc) and tc!=0)]
            tp = sum(1 for s,a in pp if a==tgt); fp = len(pp)-tp
            fn = sum(1 for s,a in ws if a==tgt and s not in [x[0] for x in pp])
            p = tp/(tp+fp) if (tp+fp)>0 else 0
            r = tp/(tp+fn) if (tp+fn)>0 else 0
            f1 = 2*p*r/(p+r) if (p+r)>0 else 0
            if f1 > best['f1']: best = {'th':tc,'p':round(p,4),'r':round(r,4),'f1':round(f1,4)}
        th[tgt] = best
    return th

def predict_model(dim_scores, weights, th):
    ts=0; tw=0
    for dim_zh, w in weights.items():
        sc = dim_scores.get(dim_zh, 0)
        if abs(sc) > 0.01: ts += sc*w; tw += w
    final = ts/tw if tw > 0 else 0
    if final > th.get('胜',{}).get('th',0.1): return '胜'
    elif final < -th.get('负',{}).get('th',0.1): return '负'
    return '平'

def predict_hand(dim_scores):
    """手拍引擎预测"""
    total = 0; n = 0
    for dim_zh in DIM_ZH:
        sc = dim_scores.get(dim_zh, 0)
        if abs(sc) > 0.1:
            total += sc
            n += 1
    if n == 0: return '平'
    avg = total / n
    if avg > 0.15: return '胜'
    elif avg < -0.15: return '负'
    return '平'

def main():
    samples = load_data()
    random.shuffle(samples)
    
    n_test = max(1, len(samples) // 10)  # 10%
    train = samples[n_test:]
    test = samples[:n_test]
    
    print(f'总样本: {len(samples)}')
    print(f'训练集: {len(train)} 测试集: {len(test)}')
    
    # 训练
    weights = learn_weights(train)
    th = learn_thresholds(train, weights)
    
    # 测试
    model_correct = 0
    hand_correct = 0
    total = len(test)
    model_by_actual = defaultdict(lambda: {'correct':0,'total':0})
    hand_by_actual = defaultdict(lambda: {'correct':0,'total':0})
    
    for s in test:
        actual = s['actual']
        dims = s['dim_scores']
        
        # 数据驱动
        mp = predict_model(dims, weights, th)
        if mp == actual: model_correct += 1
        model_by_actual[actual]['total'] += 1
        if mp == actual: model_by_actual[actual]['correct'] += 1
        
        # 手拍
        hp = predict_hand(dims)
        if hp == actual: hand_correct += 1
        hand_by_actual[actual]['total'] += 1
        if hp == actual: hand_by_actual[actual]['correct'] += 1
    
    # 基线（全猜胜）
    baseline = sum(1 for s in test if s['actual'] == '胜') / total if total > 0 else 0
    
    print(f'\n对比结果:')
    print(f'  基线（全猜胜）: {baseline:.1%}')
    print(f'  手拍引擎: {hand_correct}/{total} ({hand_correct/total:.1%})')
    print(f'  数据驱动: {model_correct}/{total} ({model_correct/total:.1%})')
    
    print(f'\n手拍分赛果:')
    for k in ['胜','平','负']:
        d = hand_by_actual[k]
        print(f'  实际{k}: {d["correct"]}/{d["total"]} ({d["correct"]/max(d["total"],1):.1%})')
    
    print(f'\n数据驱动分赛果:')
    for k in ['胜','平','负']:
        d = model_by_actual[k]
        print(f'  实际{k}: {d["correct"]}/{d["total"]} ({d["correct"]/max(d["total"],1):.1%})')
    
    # 输出权重
    print(f'\n训练权重:')
    for dim_zh in sorted(weights, key=lambda x: -weights[x]):
        print(f'  {dim_zh}: {weights[dim_zh]:.3f}')
    print(f'\n阈值:')
    for tgt, info in th.items():
        print(f'  {tgt}: th={info["th"]:+.3f} p={info["p"]:.0%} r={info["r"]:.0%}')

if __name__ == '__main__':
    main()
