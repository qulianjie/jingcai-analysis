# -*- coding: utf-8 -*-
"""用完整训练数据训练数据驱动模型 + 交叉验证"""
import json, math, os
from collections import defaultdict

DIM_ZH = ['欧赔趋势','竞彩同赔','IW同赔','澳门亚盘','让球同赔','主队主场','客队客场','百家对比','盘路匹配','庄家盈亏']
DIM_EN = ['europe_odds','jc_same','iw_same','macau_asian','rq_same','home_team','away_team','baijia','panlu','zhuangjia']
DIM_MAP = dict(zip(DIM_ZH, DIM_EN))
DIM_MAP_R = dict(zip(DIM_EN, DIM_ZH))

DATA_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\training_data.json'
OUT_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\model_v2.json'

def wilson(c,t,z=1.96):
    if t==0: return 0.0
    p=c/t; z2=z*z
    return (p+z2/(2*t)-z*math.sqrt((p*(1-p)+z2/(4*t))/t))/(1+z2/t)

def load_data():
    data = json.load(open(DATA_PATH,'r',encoding='utf-8'))
    return data['samples']

def dim_score(sample, dim_zh):
    """提取维度分，没有则返回0"""
    return sample['dim_scores'].get(dim_zh, 0.0)

def compute_score(sample, weights):
    """加权综合分"""
    ts = 0; tw = 0
    for dim_zh, w in weights.items():
        sc = dim_score(sample, dim_zh)
        ts += sc * w
        tw += w
    return ts / tw if tw > 0 else 0

def cross_validate(samples, k=5):
    """K折交叉验证训练权重和阈值"""
    n = len(samples)
    fold_size = n // k
    results = []
    
    for fold in range(k):
        val_start = fold * fold_size
        val_end = val_start + fold_size if fold < k-1 else n
        train = samples[:val_start] + samples[val_end:]
        val = samples[val_start:val_end]
        
        # 在训练集上学权重
        weights = learn_weights(train)
        # 学阈值
        th = learn_thresholds(train, weights)
        # 在验证集上评测
        correct = 0; total = 0
        for s in val:
            sc = compute_score(s, weights)
            pred = predict(sc, th)
            total += 1
            if pred == s['actual']: correct += 1
        acc = correct / total if total > 0 else 0
        results.append({'fold': fold, 'accuracy': acc, 'n': total})
    
    return results

def learn_weights(samples):
    """从数据学最优权重"""
    weights = {}
    for dim_zh in DIM_ZH:
        pairs = [(dim_score(s, dim_zh), s['actual']) for s in samples]
        pairs = [(s,a) for s,a in pairs if abs(s) > 0.01]  # 只有有信号的
        if len(pairs) < 10:
            weights[dim_zh] = 1.0 / len(DIM_ZH)  # 均匀
            continue
        # 算lift
        base_home = sum(1 for _,a in pairs if a=='胜') / len(pairs)
        pos = [(s,a) for s,a in pairs if s > 0.1]
        neg = [(s,a) for s,a in pairs if s < -0.1]
        pos_acc = sum(1 for _,a in pos if a=='胜') / len(pos) if pos else base_home
        neg_acc = sum(1 for _,a in neg if a=='负') / len(neg) if neg else base_home
        lift = max(pos_acc/max(base_home,0.01), neg_acc/max(base_home,0.01))
        w = max(0.5, min(2.0, lift))  # 权重系数 0.5~2.0
        weights[dim_zh] = w
    # 归一化
    tw = sum(weights.values())
    if tw > 0:
        for k in weights: weights[k] /= tw
    return weights

def learn_thresholds(samples, weights):
    """在训练集上学最优阈值"""
    ws = [(compute_score(s, weights), s['actual']) for s in samples]
    th = {}
    for tgt in ('胜','平','负'):
        best = {'th':0,'p':0,'r':0,'f1':0,'n':0,'correct':0}
        for tc in [x/100 for x in range(-50,51,3)]:
            pred_set = [(s,a) for s,a in ws if 
                       (tgt=='胜' and s>tc) or 
                       (tgt=='负' and s<-tc) or 
                       (tgt=='平' and abs(s)<abs(tc) and tc!=0)]
            tp = sum(1 for s,a in pred_set if a==tgt)
            fp = len(pred_set)-tp
            fn = sum(1 for s,a in ws if a==tgt and s not in [x[0] for x in pred_set])
            p = tp/(tp+fp) if (tp+fp)>0 else 0
            r = tp/(tp+fn) if (tp+fn)>0 else 0
            f1 = 2*p*r/(p+r) if (p+r)>0 else 0
            if f1 > best['f1']:
                best = {'th':tc,'p':round(p,4),'r':round(r,4),'f1':round(f1,4),'n':len(pred_set),'correct':tp}
        th[tgt] = best
    return th

def predict(score, thresholds):
    """用阈值预测赛果"""
    if score > thresholds.get('胜',{}).get('th',0.1): return '胜'
    elif score < -thresholds.get('负',{}).get('th',0.1): return '负'
    else: return '平'

def calibrate_confidence(samples, weights):
    """校准置信度：对每个综合分区间统计真实胜率"""
    ws = [(compute_score(s, weights), s['actual']) for s in samples]
    buckets = [(round(i*0.1,1), round((i+1)*0.1,1)) for i in range(-10, 10)]
    cal = {}
    for lo, hi in buckets:
        group = [a for s,a in ws if lo <= s < hi]
        if len(group) < 5: continue
        total = len(group)
        for result in ('胜','平','负'):
            correct = sum(1 for a in group if a==result)
            cal[f'{lo:.1f}_{hi:.1f}_{result}'] = {
                'total': total, 'correct': correct,
                'accuracy': round(correct/total, 3),
                'wilson': round(wilson(correct, total), 3),
            }
    return cal

def full_train(samples):
    """全量训练"""
    weights = learn_weights(samples)
    thresholds = learn_thresholds(samples, weights)
    cal = calibrate_confidence(samples, weights)
    
    # 回测
    correct = 0; total = 0
    pred_dist = defaultdict(int)
    for s in samples:
        sc = compute_score(s, weights)
        pred = predict(sc, thresholds)
        total += 1
        if pred == s['actual']: correct += 1
        pred_dist[pred] += 1
    
    # 分赛果准确率
    by_actual = defaultdict(lambda: {'correct':0,'total':0})
    for s in samples:
        sc = compute_score(s, weights)
        pred = predict(sc, thresholds)
        by_actual[s['actual']]['total'] += 1
        if pred == s['actual']: by_actual[s['actual']]['correct'] += 1
    
    return {
        'weights': weights,
        'thresholds': thresholds,
        'calibration': cal,
        'benchmark': {
            'total': total,
            'correct': correct,
            'accuracy': round(correct/total, 4),
            'by_actual': {k: {'total':v['total'],'correct':v['correct'],'acc':round(v['correct']/v['total'],3) if v['total']>0 else 0} for k,v in by_actual.items()},
            'pred_distribution': dict(pred_dist),
        }
    }

def main():
    samples = load_data()
    print(f'加载 {len(samples)} 条训练样本')
    
    # 统计各维度覆盖率
    for dim_zh in DIM_ZH:
        n = sum(1 for s in samples if dim_zh in s['dim_scores'])
        print(f'  {dim_zh}: {n}/{len(samples)} ({n/len(samples)*100:.0f}%)')
    
    # K折交叉验证
    print('\n5折交叉验证:')
    cv = cross_validate(samples, k=5)
    for r in cv:
        print(f'  折{r["fold"]}: acc={r["accuracy"]:.1%} n={r["n"]}')
    avg_acc = sum(r['accuracy'] for r in cv) / len(cv)
    print(f'  平均准确率: {avg_acc:.1%}')
    
    # 全量训练
    print('\n全量训练...')
    model = full_train(samples)
    
    print('\n学习到的权重:')
    for dim_zh in sorted(model['weights'], key=lambda x: -model['weights'][x]):
        w = model['weights'][dim_zh]
        n = sum(1 for s in samples if dim_zh in s['dim_scores'])
        print(f'  {dim_zh:10s} w={w:.3f} 样本={n}')
    
    print('\n阈值:')
    for tgt, info in model['thresholds'].items():
        print(f'  {tgt}: th={info["th"]:+.3f} p={info["p"]:.0%} r={info["r"]:.0%} f1={info["f1"]:.3f}')
    
    print(f'\n回测:')
    bm = model['benchmark']
    print(f'  总: {bm["total"]} 正确: {bm["correct"]} 准确率: {bm["accuracy"]:.1%}')
    for k, v in bm['by_actual'].items():
        print(f'  实际{k}: {v["correct"]}/{v["total"]} ({v["acc"]:.1%})')
    print(f'  预测分布: {bm["pred_distribution"]}')
    
    # 保存模型
    model['version'] = 3
    model['trained_at'] = str(__import__('datetime').datetime.now())
    model['total_samples'] = len(samples)
    model['cross_validation'] = {'accuracy_avg': round(avg_acc, 4), 'folds': cv}
    
    with open(OUT_PATH,'w',encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f'\n✅ 模型已保存: {OUT_PATH}')

if __name__ == '__main__':
    main()
