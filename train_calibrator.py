# -*- coding: utf-8 -*-
"""训练校准器"""
import json, math, os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FB_PATH = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
OUT_PATH = os.path.join(SCRIPT_DIR, 'learnings', 'calibrated_model.json')
DIM_MAP = {'欧赔趋势':'europe_odds','竞彩同赔':'jc_same','IW同赔':'iw_same','澳门亚盘':'macau_asian','让球同赔':'rq_same','主队主场':'home_team','客队客场':'away_team','百家对比':'baijia','盘路匹配':'panlu','庄家盈亏':'zhuangjia'}
DIM_ZH = {v:k for k,v in DIM_MAP.items()}

def load_feedback():
    with open(FB_PATH,'r',encoding='utf-8') as f: fb = json.load(f)
    samples = []
    for date_str, day_data in fb.get('dates',{}).items():
        if date_str=='--date': continue
        for rec in day_data.get('feedback',[]):
            actual = rec.get('actual','')
            if actual not in ('胜','平','负'): continue
            c = rec.get('combos',{})
            ds = {}
            for zh,en in DIM_MAP.items():
                v = c.get(zh+'_score') or rec.get(zh+'_score')
                if v is not None:
                    try: ds[en] = float(v)
                    except: pass
            ws = {}
            for zh,en in DIM_MAP.items():
                w = c.get(zh+'_weight')
                if w is not None:
                    try: ws[en] = float(w)/100.0
                    except: pass
            samples.append({'date':date_str,'match_num':rec.get('match_num',''),'league':rec.get('league',''),'actual':actual,'prediction':rec.get('prediction') or rec.get('predicted',''),'dim_scores':ds,'weights':ws})
    return samples

def wilson(c,t,z=1.96):
    if t==0: return 0.0
    p=c/t; z2=z*z
    return (p+z2/(2*t)-z*math.sqrt((p*(1-p)+z2/(4*t))/t))/(1+z2/t)

def cal_dim(samples,dn):
    p=[(s['dim_scores'][dn],s['actual']) for s in samples if dn in s['dim_scores']]
    if len(p)<10: return None
    ds={}
    for lb,cond in [('pos',lambda x:x>0.1),('neg',lambda x:x<-0.1),('neu',lambda x:-0.1<=x<=0.1)]:
        g=[(sc,r) for sc,r in p if cond(sc)]
        if len(g)<5: continue
        t=len(g)
        for r2 in ('胜','平','负'):
            c=sum(1 for _,a in g if a==r2)
            if c>0: ds[f'{lb}_{r2}']={'total':t,'correct':c,'acc':round(c/t,4),'wilson':round(wilson(c,t),4)}
    return {'n':len(p),'mean':round(sum(s for s,_ in p)/len(p),4),'dir':ds}

def learn_weights(samples):
    r={}
    for dn in DIM_MAP.values():
        p=[(s['dim_scores'][dn],s['actual']) for s in samples if dn in s['dim_scores']]
        if len(p)<20: r[dn]={'w':0.07,'samples':len(p),'lift':1.0}; continue
        pos_h=sum(1 for s,a in p if s>0.1 and a=='胜'); pos_t=sum(1 for s,_ in p if s>0.1)
        neg_a=sum(1 for s,a in p if s<-0.1 and a=='负'); neg_t=sum(1 for s,_ in p if s<-0.1)
        br=sum(1 for _,a in p if a=='胜')/len(p)
        pa=pos_h/pos_t if pos_t>0 else br; na=neg_a/neg_t if neg_t>0 else br
        lift=max(pa/max(br,0.01),na/max(br,0.01))
        ag=max(pa-br,na-br)
        w=max(0.05,min(0.20,0.10*min(lift,3.0)))
        r[dn]={'w':round(w,4),'samples':len(p),'lift':round(lift,3),'gain':round(ag,4),'pos_acc':round(pa,4),'neg_acc':round(na,4),'base_rate':round(br,4)}
    tw=sum(d['w'] for d in r.values())
    if tw>0:
        for d in r.values(): d['w']=round(d['w']/tw,4)
    return r

def learn_thresh(samples,weights):
    ws=[]
    for s in samples:
        ts=0; tw=0
        for dn,wi in weights.items():
            sc=s['dim_scores'].get(dn); w=wi['w']
            if sc is not None: ts+=sc*w; tw+=w
        if tw>0: ws.append((ts/tw,s['actual']))
    if len(ws)<20: return {}
    th={}
    for tgt in ('胜','平','负'):
        best={'th':0,'p':0,'r':0,'f1':0,'n':0}
        for tc in [x/100 for x in range(-50,51,5)]:
            pp=[(s,a) for s,a in ws if (tgt=='胜' and s>tc) or (tgt=='负' and s<-tc) or (tgt=='平' and abs(s)<tc)]
            tp=sum(1 for s,a in pp if a==tgt); fp=len(pp)-tp
            fn=sum(1 for s,a in ws if a==tgt and s not in [x[0] for x in pp])
            precision=tp/(tp+fp) if (tp+fp)>0 else 0
            recall=tp/(tp+fn) if (tp+fn)>0 else 0
            f1=2*precision*recall/(precision+recall) if (precision+recall)>0 else 0
            if f1>best['f1']: best={'th':tc,'p':round(precision,4),'r':round(recall,4),'f1':round(f1,4),'n':len(pp),'correct':tp}
        th[tgt]=best
    return th

def compute_score(s, dim_w):
    ts=0; tw=0
    for dn,wi in dim_w.items():
        sc=s['dim_scores'].get(dn); w=wi['w']
        if sc is not None: ts+=sc*w; tw+=w
    return ts/tw if tw>0 else 0

def main():
    samples=load_feedback()
    with_dims=[s for s in samples if s['dim_scores']]
    print(f'Samples: {len(samples)}, with dims: {len(with_dims)}')
    calibrations={}
    for en in DIM_MAP.values():
        cal=cal_dim(samples,en)
        if cal: calibrations[en]=cal; print(f'  {DIM_ZH[en]:10s} n={cal["n"]:4d}')
    dim_w=learn_weights(samples)
    print('\nWeights:')
    for en,info in sorted(dim_w.items(),key=lambda x:-x[1]['w']):
        print(f'  {DIM_ZH[en]:10s} w={info["w"]:.3f} lift={info.get("lift",1):.2f} gain={info.get("gain",0):.3f}')
    th=learn_thresh(samples,dim_w)
    print('\nThresholds:')
    for r2,info in th.items():
        print(f'  {r2}: th={info.get("th",0):+.3f} p={info.get("p",0):.1%} r={info.get("r",0):.1%} f1={info.get("f1",0):.3f}')
    correct=0; t=0
    for s in with_dims:
        sc=compute_score(s,dim_w)
        t+=1
        if sc>th.get('胜',{}).get('th',0.1) and s['actual']=='胜': correct+=1
        elif sc<-th.get('负',{}).get('th',0.1) and s['actual']=='负': correct+=1
        elif abs(sc)<=th.get('平',{}).get('th',0.1) and s['actual']=='平': correct+=1
    print(f'\nBacktest: {t} correct={correct} acc={correct/t:.1%}' if t>0 else 'No data')
    model={'version':2,'trained_at':str(__import__('datetime').datetime.now()),'total_samples':len(with_dims),'dim_weights':dim_w,'thresholds':th,'calibrations':calibrations,'benchmark':{'total':t,'correct':correct,'accuracy':round(correct/t,4) if t>0 else 0}}
    with open(OUT_PATH,'w',encoding='utf-8') as f: json.dump(model,f,ensure_ascii=False,indent=2)
    print(f'Saved: {OUT_PATH}')
if __name__=='__main__': main()
