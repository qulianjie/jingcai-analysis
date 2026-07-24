# -*- coding: utf-8 -*-
"""B方案验证：Softmax回归(mini-batch) + 90/10交叉验证 + 完整指标
   完全独立，只用numpy/csv/json
"""
import json, os, csv, random, math, io
import numpy as np
from collections import defaultdict

CSV_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\cache_feature_matrix.csv'
OUT_PATH = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\cache_model_results.json'

LABELS = ['胜', '平', '负']
FEATURE_NAMES = [
    'home_win_odds', 'draw_odds', 'away_win_odds',
    'handicap_line', 'home_moneyline', 'away_moneyline',
    'implied_prob_home', 'odds_diff_draw', 'odds_diff_away',
]


class SoftmaxRegression:
    """Softmax回归，mini-batch SGD，float32省内存"""
    def __init__(self, n_features, n_classes=3, reg=0.1, lr=0.01, epochs=20, batch_size=1024):
        self.W = np.random.randn(n_features, n_classes).astype(np.float32) * 0.01
        self.b = np.zeros((1, n_classes), dtype=np.float32)
        self.reg = reg; self.lr = lr
        self.epochs = epochs; self.batch_size = batch_size

    def softmax(self, z):
        zm = np.max(z, axis=1, keepdims=True)
        ez = np.exp(z - zm)
        s = np.sum(ez, axis=1, keepdims=True); s[s==0] = 1
        return ez / s

    def fit(self, X, y):
        n = X.shape[0]
        for ep in range(self.epochs):
            idx = np.random.permutation(n)
            Xs, ys = X[idx], y[idx]
            for start in range(0, n, self.batch_size):
                end = min(start + self.batch_size, n)
                Xb, yb = Xs[start:end], ys[start:end]
                bs = Xb.shape[0]
                sc = Xb @ self.W + self.b
                pr = self.softmax(sc)
                gr = pr.copy(); gr[np.arange(bs), yb] -= 1
                dW = (Xb.T @ gr) / bs + self.reg * self.W
                db = np.sum(gr, axis=0, keepdims=True) / bs
                self.W -= self.lr * dW; self.b -= self.lr * db
            self.lr *= 0.995

    def predict(self, X):
        return np.argmax(self.softmax(X @ self.W + self.b), axis=1)


def load_data():
    features, targets = [], []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        rdr = csv.reader(f); next(rdr)
        for row in rdr:
            if len(row) != 10: continue
            features.append([float(v) for v in row[:9]])
            t = row[9]
            targets.append(0 if t == '\u80dc' else 1 if t == '\u5e73' else 2)
    X = np.array(features, dtype=np.float32)
    y = np.array(targets, dtype=np.int32)
    return X, y


def calc_metrics(y_true, y_pred):
    cm = np.zeros((3,3), dtype=int)
    for t,p in zip(y_true, y_pred): cm[t][p] += 1
    metrics = {}
    for i, nm in enumerate(LABELS):
        tp = cm[i][i]; fp = int(sum(cm[j][i] for j in range(3) if j!=i))
        fn = int(sum(cm[i][j] for j in range(3) if j!=i))
        pr = tp/(tp+fp) if (tp+fp)>0 else 0.0
        re = tp/(tp+fn) if (tp+fn)>0 else 0.0
        f1 = 2*pr*re/(pr+re) if (pr+re)>0 else 0.0
        metrics[nm] = {'precision':round(float(pr),4),'recall':round(float(re),4),
                       'f1':round(float(f1),4),'support':int(tp+fn)}
    total = len(y_true)
    acc = sum(1 for t,p in zip(y_true,y_pred) if t==p)/total if total>0 else 0.0
    macro_f1 = sum(m['f1'] for m in metrics.values())/3
    ts = sum(m['support'] for m in metrics.values()) or 1
    wf1 = sum(m['f1']*m['support'] for m in metrics.values())/ts
    dist = defaultdict(int)
    for t in y_true: dist[t] += 1
    bc = max(dist, key=dist.get) if dist else 0
    bl = dist[bc]/total if total>0 else 0.0
    return {'per_class':metrics,'accuracy':round(float(acc),4),'macro_f1':round(float(macro_f1),4),
            'weighted_f1':round(float(wf1),4),'baseline':round(float(bl),4),
            'improvement':round(float(acc-bl),4)}


def avg_metrics(results):
    avg = {'accuracy':round(float(np.mean([r['accuracy'] for r in results])),4),
           'macro_f1':round(float(np.mean([r['macro_f1'] for r in results])),4),
           'weighted_f1':round(float(np.mean([r['weighted_f1'] for r in results])),4),
           'baseline':round(float(np.mean([r['baseline'] for r in results])),4),
           'improvement':round(float(np.mean([r['improvement'] for r in results])),4),
           'per_class':{}}
    for lb in LABELS:
        avg['per_class'][lb] = {
            'precision':round(float(np.mean([r['per_class'][lb]['precision'] for r in results])),4),
            'recall':round(float(np.mean([r['per_class'][lb]['recall'] for r in results])),4),
            'f1':round(float(np.mean([r['per_class'][lb]['f1'] for r in results])),4)}
    return avg


def run():
    print('Loading...')
    X_all, y_all = load_data()
    total = len(X_all)
    print(f'{total} samples: H={int(np.sum(y_all==0))} D={int(np.sum(y_all==1))} A={int(np.sum(y_all==2))}')
    print(f'Features: {X_all.shape[1]}')

    # normalize
    mu = np.mean(X_all, axis=0); sd = np.std(X_all, axis=0); sd[sd==0]=1
    Xn = (X_all - mu) / sd

    results = []
    for it in range(10):
        idx = list(range(total))
        random.shuffle(idx)
        ts = max(1, total//10)
        tr, te = idx[ts:], idx[:ts]
        Xtr, Xte = Xn[tr], Xn[te]
        ytr, yte = y_all[tr], y_all[te]
        model = SoftmaxRegression(Xtr.shape[1])
        model.fit(Xtr, ytr)
        preds = model.predict(Xte)
        metrics = calc_metrics(yte, preds)
        results.append(metrics)
        if (it+1)%3==0:
            print(f'  Fold {it+1}/10: acc={metrics["accuracy"]:.1%} f1={metrics["weighted_f1"]:.3f}')

    avg = avg_metrics(results)
    print()
    print('='*55)
    print('  B: Raw Odds -> Softmax (90/10 x10)')
    print('='*55)
    print(f'  Samples:      {total}')
    print(f'  Accuracy:     {avg["accuracy"]:.1%}')
    print(f'  Macro F1:     {avg["macro_f1"]:.3f}')
    print(f'  Weighted F1:  {avg["weighted_f1"]:.3f}')
    print(f'  Baseline:     {avg["baseline"]:.1%}')
    print(f'  Over base:    {avg["improvement"]:+.1%}')
    print(f'\n  Label  Prec   Rec    F1')
    print(f'  {"-"*30}')
    for lb in LABELS:
        m = avg['per_class'][lb]
        print(f'  {lb}  {m["precision"]:.1%}  {m["recall"]:.1%}  {m["f1"]:.3f}')

    json.dump({'method':'B-raw-odds-softmax','n_samples':total,'feature_names':FEATURE_NAMES,
               'results':results,'average':avg},
              open(OUT_PATH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f'\nSaved: {OUT_PATH}')


if __name__ == '__main__':
    run()
/bin/bash: line 4: C:/Users/lianjie/.hermes/cache/terminal/hermes-snap-40d25c58b2e9.sh: No such file or directory
/bin/bash: line 5: C:/Users/lianjie/.hermes/cache/terminal/hermes-cwd-40d25c58b2e9.txt: No such file or directory
