# -*- coding: utf-8 -*-
"""B方案XGBoost调参 — 权重/深度/学习率扫描"""
import json, random, gc, time
import numpy as np
import xgboost as xgb

CSV='C:/Users/lianjie/.openclaw/workspace/jingcai/learnings/cache_feature_matrix.csv'
OUT='C:/Users/lianjie/.openclaw/workspace/jingcai/learnings/cache_model_results.json'
L=['胜','平','负']

def load():
    print('Loading...')
    dt=np.dtype([('f',np.float32,9),('t',np.int32)])
    def g():
        with open(CSV,'r',encoding='utf-8') as f:
            next(f)
            for line in f:
                p=line.strip().split(',')
                if len(p)!=10:continue
                yield ([float(v) for v in p[:9]],0 if p[9]=='胜' else 1 if p[9]=='平' else 2)
    a=np.fromiter(g(),dtype=dt,count=-1)
    print(f'  {len(a)} samples')
    return a['f'],a['t']

def met(yt,yp):
    cm=np.zeros((3,3),dtype=int)
    for t,p in zip(yt,yp):cm[t][p]+=1
    m={}
    for i,lb in enumerate(L):
        tp=cm[i,i];fp=int(cm[:,i].sum())-tp;fn=int(cm[i,:].sum())-tp
        pr=tp/(tp+fp)if tp+fp>0 else 0;re=tp/(tp+fn)if tp+fn>0 else 0
        f1=2*pr*re/(pr+re)if pr+re>0 else 0
        m[lb]={'precision':round(float(pr),4),'recall':round(float(re),4),'f1':round(float(f1),4),'support':int(tp+fn)}
    t=len(yt);a=sum(1 for t2,p in zip(yt,yp)if t2==p)/t
    mf=sum(v['f1']for v in m.values())/3
    ts=sum(v['support']for v in m.values())or 1
    wf=sum(v['f1']*v['support']for v in m.values())/ts
    dc={int(k):int(v)for k,v in zip(*np.unique(yt,return_counts=True))}
    bc=max(dc,key=dc.get);bl=dc[bc]/t
    return {'per_class':m,'accuracy':round(float(a),4),'macro_f1':round(float(mf),4),'weighted_f1':round(float(wf),4),'baseline':round(float(bl),4)}

def single_fold(X,y,tri,tei,params,class_weights):
    sw = np.array([class_weights[t] for t in y[tri]], dtype=np.float32)
    dtrain = xgb.DMatrix(X[tri], label=y[tri], weight=sw)
    dtest = xgb.DMatrix(X[tei])
    model = xgb.train(params, dtrain, num_boost_round=params.get('n_estimators',200), verbose_eval=False)
    pr = model.predict(dtest).argmax(axis=1)
    return met(y[tei], pr)

def evaluate_config(X,y,params,cw_name,class_weights,n_folds=5):
    """用5折快速评估一组参数"""
    n=len(X);idx=list(range(n));random.shuffle(idx)
    ts=n//n_folds;folds=[idx[i*ts:(i+1)*ts] if i<n_folds-1 else idx[i*ts:] for i in range(n_folds)]
    rs=[]
    for fold_idx in folds:
        tri=[i for i in idx if i not in fold_idx];tei=fold_idx
        rs.append(single_fold(X,y,np.array(tri),np.array(tei),params,class_weights))
        gc.collect()
    a={'accuracy':np.mean([r['accuracy']for r in rs]),'macro_f1':np.mean([r['macro_f1']for r in rs]),
       'weighted_f1':np.mean([r['weighted_f1']for r in rs])}
    return a

def run():
    X,y=load()
    dist=np.bincount(y)
    print(f'Dist: 胜={dist[0]} 平={dist[1]} 负={dist[2]}')
    
    # 参数扫描
    configs=[]
    
    # 权重方案
    weight_schemes = [
        ('inv_freq', [1.0, dist[0]/dist[1], dist[0]/dist[2]]),  # 1:1.9:1.28 (当前)
        ('balanced', [dist.sum()/(3*dist[0]), dist.sum()/(3*dist[1]), dist.sum()/(3*dist[2])]),  # sklearn balanced
        ('heavy_draw', [1.0, 3.0, 1.0]),  # 平局重权
        ('draw_focus', [1.0, 4.0, 1.0]),  # 平局更重
        ('moderate', [1.0, 2.5, 1.5]),    # 平局加重+客胜稍重
    ]
    
    # 树参数
    tree_configs = [
        {'max_depth':6, 'eta':0.1, 'n_estimators':200, 'min_child_weight':3},
        {'max_depth':8, 'eta':0.08, 'n_estimators':250, 'min_child_weight':2},
        {'max_depth':4, 'eta':0.15, 'n_estimators':150, 'min_child_weight':5},
        {'max_depth':6, 'eta':0.05, 'n_estimators':400, 'min_child_weight':3},
        {'max_depth':10, 'eta':0.1, 'n_estimators':150, 'min_child_weight':1},
    ]
    
    base_params = {
        'objective':'multi:softprob','num_class':3,
        'subsample':0.8,'colsample_bytree':0.8,
        'seed':42,
    }
    
    print(f'\n扫描 {len(weight_schemes)*len(tree_configs)} 组参数 (5折快速)...\n')
    results=[]
    for tc in tree_configs:
        for cw_name,cw in weight_schemes:
            params={**base_params,**tc}
            start=time.time()
            a=evaluate_config(X,y,params,cw_name,cw)
            elapsed=time.time()-start
            configs.append({**a,'cw_name':cw_name,'cw':[round(w,2)for w in cw],
                           'depth':tc['max_depth'],'eta':tc['eta'],'n_est':tc['n_estimators'],
                           'time':round(elapsed,1)})
            print(f'  d={tc["max_depth"]} eta={tc["eta"]} {cw_name:12s} '
                  f'acc={a["accuracy"]:.1%} mf1={a["macro_f1"]:.3f} wf1={a["weighted_f1"]:.3f} ({elapsed:.0f}s)')
            results.append(configs[-1])
    
    # 按macro_f1排序
    results.sort(key=lambda x:-x['macro_f1'])
    best=results[0]
    
    print(f'\n{"="*55}')
    print(f'最佳参数 (按Macro F1)')
    print(f'{"="*55}')
    print(f'  权重: {best["cw_name"]} {best["cw"]}')
    print(f'  树深: {best["depth"]}  lr: {best["eta"]}  迭代: {best["n_est"]}')
    print(f'  Acc: {best["accuracy"]:.1%}  MF1: {best["macro_f1"]:.3f}  WF1: {best["weighted_f1"]:.3f}')
    
    # Top 5
    print(f'\nTop 5:')
    for r in results[:5]:
        print(f'  {r["cw_name"]:12s} d={r["depth"]} eta={r["eta"]} '
              f'acc={r["accuracy"]:.1%} mf1={r["macro_f1"]:.3f} wf1={r["weighted_f1"]:.3f}')
    
    # 用最佳参数跑完整10折
    print(f'\n{"="*55}')
    print(f'最佳参数 → 10折完整验证')
    print(f'{"="*55}')
    best_params = {**base_params, 'max_depth':best['depth'], 'eta':best['eta'], 'n_estimators':best['n_est'],
                   'min_child_weight':3 if best['depth']>=6 else 5}
    best_cw = best['cw']
    
    n=len(X);idx=list(range(n));rs10=[]
    for fold in range(10):
        random.shuffle(idx);ts=n//10;tri,tei=idx[ts:],idx[:ts]
        sw=np.array([best_cw[t] for t in y[tri]],dtype=np.float32)
        dtrain=xgb.DMatrix(X[tri],label=y[tri],weight=sw)
        dtest=xgb.DMatrix(X[tei])
        model=xgb.train(best_params,dtrain,num_boost_round=best_params['n_estimators'],verbose_eval=False)
        pr=model.predict(dtest).argmax(axis=1)
        rs10.append(met(y[tei],pr))
        gc.collect()
        if(fold+1)%3==0:print(f'  F{fold+1}/10: acc={rs10[-1]["accuracy"]:.1%} mf1={rs10[-1]["macro_f1"]:.3f}')
    
    a10={k:round(float(np.mean([r[k]for r in rs10])),4)for k in['accuracy','macro_f1','weighted_f1']}
    print(f'\n10折最终:')
    print(f'  Acc: {a10["accuracy"]:.1%}  MF1: {a10["macro_f1"]:.3f}  WF1: {a10["weighted_f1"]:.3f}')
    
    per_class={}
    for lb in L:
        per_class[lb]={k:round(float(np.mean([r['per_class'][lb][k]for r in rs10])),4)for k in['precision','recall','f1']}
    print(f'\n  {"Label":>4s} {"Prec":>7s} {"Rec":>7s} {"F1":>7s}')
    for lb in L:
        m=per_class[lb];print(f'  {lb:>4s} {m["precision"]:.1%} {m["recall"]:.1%} {m["f1"]:.3f}')
    
    json.dump({'method':'B-xgboost-tuned','best_params':best,'final_10fold':a10,'per_class':per_class,'all_results':results},
              open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f'\nSaved: {OUT}')

if __name__=='__main__':run()
