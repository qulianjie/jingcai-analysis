# -*- coding: utf-8 -*-
"""90/10验证+完整指标：精确率/召回率/F1/混淆矩阵"""
import json, math, random
from collections import defaultdict

DATA_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\training_data.json'
DIM_ZH = ['欧赔趋势','竞彩同赔','IW同赔','澳门亚盘','让球同赔','主队主场','客队客场','百家对比','盘路匹配','庄家盈亏']

def load_data():
    data = json.load(open(DATA_PATH,'r',encoding='utf-8'))
    return data['samples']

def calc_metrics(y_true, y_pred, labels=['胜','平','负']):
    """计算精确率/召回率/F1/混淆矩阵"""
    cm = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1
    
    metrics = {}
    for label in labels:
        tp = cm[label][label]
        fp = sum(cm[t][label] for t in labels if t != label)
        fn = sum(cm[label][p] for p in labels if p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        metrics[label] = {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'support': tp + fn,
        }
    
    # Macro avg
    macro_f1 = sum(m['f1'] for m in metrics.values()) / len(labels)
    # Weighted avg
    total = sum(m['support'] for m in metrics.values())
    weighted_f1 = sum(m['f1'] * m['support'] for m in metrics.values()) / total if total > 0 else 0
    # Accuracy
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true) if y_true else 0
    
    return {
        'per_class': metrics,
        'accuracy': round(accuracy, 4),
        'macro_f1': round(macro_f1, 4),
        'weighted_f1': round(weighted_f1, 4),
        'confusion_matrix': cm,
    }

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
    total = 0; n = 0
    for dim_zh in DIM_ZH:
        sc = dim_scores.get(dim_zh, 0)
        if abs(sc) > 0.1: total += sc; n += 1
    if n == 0: return '平'
    avg = total / n
    if avg > 0.15: return '胜'
    elif avg < -0.15: return '负'
    return '平'

def run_validation(samples, n_iter=10):
    """多次随机90/10取平均"""
    all_hand = []
    all_model = []
    
    for it in range(n_iter):
        random.shuffle(samples)
        n_test = max(1, len(samples) // 10)
        train = samples[n_test:]
        test = samples[:n_test]
        
        weights = learn_weights(train)
        th = learn_thresholds(train, weights)
        
        y_true = [s['actual'] for s in test]
        y_hand = [predict_hand(s['dim_scores']) for s in test]
        y_model = [predict_model(s['dim_scores'], weights, th) for s in test]
        
        all_hand.append(calc_metrics(y_true, y_hand))
        all_model.append(calc_metrics(y_true, y_model))
    
    return all_hand, all_model

def avg_metrics(results):
    """多次结果平均"""
    avg = {}
    # Accuracy
    avg['accuracy'] = round(sum(r['accuracy'] for r in results) / len(results), 4)
    avg['macro_f1'] = round(sum(r['macro_f1'] for r in results) / len(results), 4)
    avg['weighted_f1'] = round(sum(r['weighted_f1'] for r in results) / len(results), 4)
    
    # Per class
    avg['per_class'] = {}
    for label in ['胜','平','负']:
        avg['per_class'][label] = {
            'precision': round(sum(r['per_class'][label]['precision'] for r in results) / len(results), 4),
            'recall': round(sum(r['per_class'][label]['recall'] for r in results) / len(results), 4),
            'f1': round(sum(r['per_class'][label]['f1'] for r in results) / len(results), 4),
        }
    return avg

def print_metrics(name, avg, samples):
    print(f'\n{"="*50}')
    print(f'{name}:')
    print(f'{"="*50}')
    print(f'  总准确率:  {avg["accuracy"]:.1%}')
    print(f'  Macro F1:  {avg["macro_f1"]:.3f}')
    print(f'  Weighted F1: {avg["weighted_f1"]:.3f}')
    print(f'\n  {"类别":>6s} {"精确率":>8s} {"召回率":>8s} {"F1":>8s} {"样本":>6s}')
    print(f'  {"-"*40}')
    for label in ['胜','平','负']:
        m = avg['per_class'][label]
        n = sum(1 for s in samples if s['actual']==label)
        print(f'  {label:>4s}  {m["precision"]:.1%}  {m["recall"]:.1%}  {m["f1"]:.3f}  {n:>4d}')
    # 基线
    total = len(samples)
    base = max(sum(1 for s in samples if s['actual']=='胜'),
               sum(1 for s in samples if s['actual']=='平'),
               sum(1 for s in samples if s['actual']=='负')) / total
    print(f'\n  基线(全猜最多类): {base:.1%}')
    print(f'  提升 vs 基线: {avg["accuracy"] - base:+.1%}')

def main():
    samples = load_data()
    print(f'加载 {len(samples)} 条训练样本')
    print(f'赛果分布: 胜={sum(1 for s in samples if s["actual"]=="胜")} 平={sum(1 for s in samples if s["actual"]=="平")} 负={sum(1 for s in samples if s["actual"]=="负")}')
    
    hand_results, model_results = run_validation(samples, n_iter=10)
    
    hand_avg = avg_metrics(hand_results)
    model_avg = avg_metrics(model_results)
    
    print_metrics('手拍规则 (现行引擎)', hand_avg, samples)
    print_metrics('数据驱动 (V2试验)', model_avg, samples)

if __name__ == '__main__':
    main()
