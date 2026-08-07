# -*- coding: utf-8 -*-
"""竞彩盘路一致性 — 13维整体匹配"""
import json,sys,os,re,time,math
from datetime import datetime
from collections import Counter
import requests
from bs4 import BeautifulSoup

SD=os.path.dirname(os.path.abspath(__file__))
TD=os.path.join(SD,'tasks')
CD=os.path.join(SD,'data','league_cache')
sess=requests.Session()
sess.headers.update({'User-Agent':'Mozilla/5.0'})

def dr(iv,lv):
 d=''
 for a,b in zip(iv,lv):
  if b>a+0.01:d+='⬆'
  elif b<a-0.01:d+='⬇'
  else:d+='➡'
 return d

def rk(v):return math.floor(v*10)/10

# 先决条件（不计入匹配计数）：av_dir, iw_dir, as_pan
PREREQ_KEYS=['av_dir','iw_dir','as_pan']
DK=['av_dir','iw_dir','as_pan','hc_dir','av_w','av_d','av_l','jc_w','jc_d','jc_l','hc_w','hc_d','hc_l','iw_w','iw_d','iw_l']
DN=['盘路_百家','盘路_IW','澳门','盘路_让球','主胜_百家','平赔_百家','客胜_百家','主胜_竞彩','平赔_竞彩','客胜_竞彩','主胜_让球','平赔_让球','客胜_让球','主胜_IW','平赔_IW','客胜_IW']

def get_ms(ds=None):
 if ds is None:ds=datetime.now().strftime('%Y-%m-%d')
 for b in[TD,os.path.join(SD,'data','tasks')]:
  p=os.path.join(b,ds,'matches_data.json')
  if os.path.exists(p):
   with open(p,'r')as f:d=json.load(f)
   ml=[]
   for gd in d.get('groups',{}).values():ml.extend(gd.get('matches',[]))
   return ml,ds
 return[],ds

def fo(fid):
 r={'jc':{},'av':{},'hc':{},'hc_iw':{},'as':{}}
 try:
  for src,key in[('ouzhi','jc'),('ouzhi','av'),('rangqiu','hc')]:
   url=f'https://odds.500.com/fenxi/{src}-{fid}.shtml'
   x=sess.get(url,timeout=10);x.encoding='gbk'
   s=BeautifulSoup(x.text,'html.parser')
   for t in s.find_all('table'):
    for tr in t.find_all('tr'):
     td=tr.find_all('td')
     if len(td)<12:continue
     t0=td[0].get_text().strip()
     if src=='ouzhi':
      if key=='jc'and t0!='1':continue
      if key=='av':
       if'平均'not in td[1].get_text()and'百家'not in td[1].get_text():continue
     elif src=='rangqiu'and t0!='1':continue
     n=[]
     for idx in[3,4,5,6,7,8]if src=='ouzhi'else[4,5,6,7,8,9]:
      try:n.append(float(td[idx].get_text().strip().replace(chr(160),'')))
      except:pass
     if len(n)<6:continue
     r[key]={'iw':n[0],'id':n[1],'il':n[2],'lw':n[3],'ld':n[4],'ll':n[5],'dir':dr(n[:3],n[3:6])}
     break
 except:pass
# rangqiu页再找IW让球行(td0='6')
 try:
  url=f'https://odds.500.com/fenxi/rangqiu-{fid}.shtml'
  x=sess.get(url,timeout=10);x.encoding='gbk'
  s=BeautifulSoup(x.text,'html.parser')
  for t in s.find_all('table'):
   for tr in t.find_all('tr'):
    td=tr.find_all('td')
    if len(td)<12:continue
    t0=td[0].get_text().strip()
    if t0!='6':continue
    n=[]
    for idx in[4,5,6,7,8,9]:
     try:n.append(float(td[idx].get_text().strip().replace(chr(160),'')))
     except:pass
    if len(n)>=6:
     r['hc_iw']={'iw':n[0],'id':n[1],'il':n[2],'lw':n[3],'ld':n[4],'ll':n[5],'dir':dr(n[:3],n[3:6])}
     break
 except:pass
# ouzhi页找IW公司盘路(塞浦路斯)
 try:
  url=f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
  x=sess.get(url,timeout=10);x.encoding='gbk'
  s=BeautifulSoup(x.text,'html.parser')
  for t in s.find_all('table'):
   for tr in t.find_all('tr'):
    td=tr.find_all('td')
    if len(td)<12:continue
    nm=td[1].get_text().strip()
    if'塞浦路斯'not in nm:continue
    n=[]
    for idx in[3,4,5,6,7,8]:
     try:n.append(float(td[idx].get_text().strip().replace(chr(160),'')))
     except:pass
    if len(n)>=6:
     r['iw_dir']=dr(n[:3],n[3:6])
     r['iw_odds']={'lw':n[3],'ld':n[4],'ll':n[5]}
     break
 except:pass
# yazhi: 从表头确认"即时盘口"/"初始盘口"顺序, ref属性找盘口名
 try:
  url=f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
  x=sess.get(url,timeout=10);x.encoding='gbk'
  s=BeautifulSoup(x.text,'html.parser')
  # 表头找即时/初始顺序
  jb=True
  for t in s.find_all('table'):
   for tr in t.find_all('tr'):
    txt=[th.get_text(strip=True)for th in tr.find_all('th')]
    if any('即时盘口'in t for t in txt)and any('初始盘口'in t for t in txt):
     jb=next((i for i,t in enumerate(txt)if'即时盘口'in t),99)<next((i for i,t in enumerate(txt)if'初始盘口'in t),99)
     break
   else:continue;break
  for t in s.find_all('table'):
   for tr in t.find_all('tr'):
    td=tr.find_all('td')
    if len(td)<12:continue
    t0=td[0].get_text().strip()
    if not t0.isdigit():continue
    n=int(t0)
    if n not in(1,2,3):continue
    nm=td[1].get_text().strip()
    # ref属性找盘口名
    rc=[i for i in range(len(td))if td[i].get('ref')and __import__('re').match(r'^-?[\d.]+$',td[i].get('ref',''))]
    if len(rc)<2:continue
    li,ii=(rc[0],rc[1])if jb else(rc[1],rc[0])
    cln=lambda t:t.replace(chr(160),'').replace('↑','').replace('↓','').replace('升','').replace('降','').strip()
    ip=cln(td[ii].get_text());lp=cln(td[li].get_text())
    try:
     ih=float(re.search(r'([\d.]+)',td[li-1].get_text()).group(1))
     il=float(re.search(r'([\d.]+)',td[li+1].get_text()).group(1))
     lh=float(re.search(r'([\d.]+)',td[ii-1].get_text()).group(1))
     ll=float(re.search(r'([\d.]+)',td[ii+1].get_text()).group(1))
    except:ih=il=lh=ll=''
    e={'name':nm,'ip':ip,'ih':lh,'il':ll,'lp':lp,'lh':ih,'ll':il}
    if'门'in nm or n==1:
     if not r['as']or'门'in nm:r['as']=e
 except:pass
 return r

def ld(league):
 cp=None;best=0;lk=''
 # 联赛名别名映射（500.com名 → 缓存文件名）
 ALIAS={'韩职':'K1联赛','K1联赛':'韩职','美职足':'美职联','美职联':'美职足',
        '英联赛杯':'英联杯','英联杯':'英联赛杯'}
 league=ALIAS.get(league,league)
 if os.path.exists(CD):
  for fn in os.listdir(CD):
   if not fn.endswith('.json'):continue
   lk=fn.replace('.json','')
   if lk==league:score=100
   elif lk.startswith(league)or league.startswith(lk):score=50
   elif league in lk or lk in league:score=10
   else:continue
   # 富集缓存加分
   try:
    with open(os.path.join(CD,fn),'r')as f:
     d=json.load(f)
    enriched=d.get('enriched_date')or d.get('enriched')
    if enriched:score+=1000
    ml_cnt=len(d.get('all_matches',[]))
    score+=ml_cnt*0.5  # 场数多也加分(权重提高，防小文件靠精确名取胜)
   except:pass
   if score>best:best=score;cp=os.path.join(CD,fn)
 if not cp or not os.path.exists(cp):return None
 with open(cp,'r')as f:d=json.load(f)
 ml=d.get('all_matches',[])
 if not ml:return None
 return{'league':d.get('league',league),'matches':ml,'total':len(ml)}

def ext_hist(hm):
 oe=hm.get('odds_europe',{})
 # 百家终盘(from oe.av), 没有则从顶层WIN/DRAW/LOST(初盘)
 av={'lw':hm.get('WIN'),'ld':hm.get('DRAW'),'ll':hm.get('LOST')}
 if isinstance(oe,dict)and oe.get('av'):
  av_av=oe['av']
  if av_av.get('lw'):av['lw']=av_av['lw']
  if av_av.get('ld'):av['ld']=av_av['ld']
  if av_av.get('ll'):av['ll']=av_av['ll']
 jc={};avd=''
 if isinstance(oe,dict):
  if oe.get('jc'):jc={'lw':oe['jc'].get('lw'),'ld':oe['jc'].get('ld'),'ll':oe['jc'].get('ll'),'dir':oe.get('dir_jc')}
  cs=oe.get('companies',[])
  if cs:
   ad=[c.get('dir','')for c in cs if c.get('dir')]
   if ad:av['dir']=Counter(ad).most_common(1)[0][0]
 oh=hm.get('odds_handicap',{})
 hc={}
 if isinstance(oh,dict):
  if oh.get('jc'):hc={'lw':oh['jc'].get('lw'),'ld':oh['jc'].get('ld'),'ll':oh['jc'].get('ll'),'dir':oh['jc'].get('dir'),'src':'竞'}
  elif oh.get('iw'):hc={'lw':oh['iw'].get('lw'),'ld':oh['iw'].get('ld'),'ll':oh['iw'].get('ll'),'dir':oh['iw'].get('dir'),'src':'IW'}
 asn={}
 oa=hm.get('odds_asian',[])
 if oa:
  for item in oa:
   if'门'in item.get('name','')or item==oa[0]:\
    asn={'ip':item.get('init_pan',''),'lp':item.get('live_pan',''),'lh':item.get('live_water_high',''),'ll':item.get('live_water_low','')};break
 return av,jc,hc,asn

def _get_iw_dir_companies(cs):
 """从companies列表找IW公司方向"""
 for c in (cs or []):
  if'塞浦路斯'in c.get('name','')and c.get('dir'):return c['dir']
 return None

def _get_iw_odds_companies(cs):
 """从companies列表找IW公司终赔"""
 for c in (cs or []):
  if'塞浦路斯'in c.get('name',''):
   if c.get('lw'):return {'lw':c['lw'],'ld':c.get('ld'),'ll':c.get('ll')}
 return None

def sr(hist,tod):
 if not hist:return None
 ml=hist['matches']
 if not ml:return None
 jc=tod.get('jc',{});av=tod.get('av',{});hc=tod.get('hc',{});hc_iw=tod.get('hc_iw',{});asn=tod.get('as',{});iw_odds=tod.get('iw_odds',{})
 tv={}
 # 让球：优先jc(竞彩让球), 没有则用iw(IW让球)
 _hc=hc if hc.get('dir') else hc_iw
 tv['av_dir']=av.get('dir','');tv['jc_dir']=jc.get('dir','');tv['iw_dir']=tod.get('iw_dir','');tv['as_pan']=asn.get('lp','');tv['as_ip']=asn.get('ip','')
 tv['hc_dir']=_hc.get('dir','');tv['hc_src']='竞' if hc.get('dir') else ('IW' if hc_iw.get('dir') else '-')
 if av.get('lw'):tv['av_w']=rk(av['lw'])
 if av.get('ld'):tv['av_d']=rk(av['ld'])
 if av.get('ll'):tv['av_l']=rk(av['ll'])
 if jc.get('lw'):tv['jc_w']=rk(jc['lw'])
 if jc.get('ld'):tv['jc_d']=rk(jc['ld'])
 if jc.get('ll'):tv['jc_l']=rk(jc['ll'])
 # 让球赔率也fallback jc→iw
 _hc_w=hc if hc.get('lw')else hc_iw
 if _hc_w.get('lw'):tv['hc_w']=rk(_hc_w['lw'])
 _hc_d=hc if hc.get('ld')else hc_iw
 if _hc_d.get('ld'):tv['hc_d']=rk(_hc_d['ld'])
 _hc_l=hc if hc.get('ll')else hc_iw
 if _hc_l.get('ll'):tv['hc_l']=rk(_hc_l['ll'])
 # IW终赔
 if iw_odds.get('lw'):tv['iw_w']=rk(iw_odds['lw'])
 if iw_odds.get('ld'):tv['iw_d']=rk(iw_odds['ld'])
 if iw_odds.get('ll'):tv['iw_l']=rk(iw_odds['ll'])

 # 提取函数：全部维度（先决条件 + 剩余变量）
 ext=[
  ('av_dir',lambda hm:Counter([c.get('dir','')for c in hm.get('odds_europe',{}).get('companies',[])if c.get('dir')]).most_common(1)[0][0]if hm.get('odds_europe',{}).get('companies')else None),
  ('iw_dir',lambda hm:_get_iw_dir_companies(hm.get('odds_europe',{}).get('companies',[]))),
  ('as_pan',lambda hm:next((item.get('live_pan')for item in(hm.get('odds_asian',[])or[])if'门'in item.get('name','')or item==(hm.get('odds_asian',[])or[{}])[0]),None)),
  ('hc_dir',lambda hm:(lambda oh:oh.get('jc',{}).get('dir')if oh.get('jc')else oh.get('iw',{}).get('dir'))(hm.get('odds_handicap',{}))if hm.get('odds_handicap')else None),
  ('av_w',lambda hm:rk(float(hm.get('odds_europe',{}).get('av',{}).get('lw')))if hm.get('odds_europe',{}).get('av',{}).get('lw')else None),
  ('av_d',lambda hm:rk(float(hm.get('odds_europe',{}).get('av',{}).get('ld')))if hm.get('odds_europe',{}).get('av',{}).get('ld')else None),
  ('av_l',lambda hm:rk(float(hm.get('odds_europe',{}).get('av',{}).get('ll')))if hm.get('odds_europe',{}).get('av',{}).get('ll')else None),
  ('jc_w',lambda hm:rk(float(hm.get('odds_europe',{}).get('jc',{}).get('lw')))if hm.get('odds_europe',{}).get('jc',{}).get('lw')else None),
  ('jc_d',lambda hm:rk(float(hm.get('odds_europe',{}).get('jc',{}).get('ld')))if hm.get('odds_europe',{}).get('jc',{}).get('ld')else None),
  ('jc_l',lambda hm:rk(float(hm.get('odds_europe',{}).get('jc',{}).get('ll')))if hm.get('odds_europe',{}).get('jc',{}).get('ll')else None),
  ('hc_w',lambda hm:(lambda oh:rk(float(oh.get('jc',{}).get('lw')))if oh.get('jc',{}).get('lw')else(rk(float(oh.get('iw',{}).get('lw')))if oh.get('iw',{}).get('lw')else None))(hm.get('odds_handicap',{}))),
  ('hc_d',lambda hm:(lambda oh:rk(float(oh.get('jc',{}).get('ld')))if oh.get('jc',{}).get('ld')else(rk(float(oh.get('iw',{}).get('ld')))if oh.get('iw',{}).get('ld')else None))(hm.get('odds_handicap',{}))),
  ('hc_l',lambda hm:(lambda oh:rk(float(oh.get('jc',{}).get('ll')))if oh.get('jc',{}).get('ll')else(rk(float(oh.get('iw',{}).get('ll')))if oh.get('iw',{}).get('ll')else None))(hm.get('odds_handicap',{}))),
  ('iw_w',lambda hm:(lambda iw:rk(float(iw.get('lw')))if iw.get('lw')else None)(_get_iw_odds_companies(hm.get('odds_europe',{}).get('companies',[])))),
  ('iw_d',lambda hm:(lambda iw:rk(float(iw.get('ld')))if iw.get('ld')else None)(_get_iw_odds_companies(hm.get('odds_europe',{}).get('companies',[])))),
  ('iw_l',lambda hm:(lambda iw:rk(float(iw.get('ll')))if iw.get('ll')else None)(_get_iw_odds_companies(hm.get('odds_europe',{}).get('companies',[])))),
 ]

 groups={};prereq_cnt=0;prereq_ml=[]
 for hm in ml:
  # 先决条件：3个维度全部精确匹配
  all_prereq_ok=True
  for k in PREREQ_KEYS:
   idx=DK.index(k)
   key,fn=ext[idx]
   tv_v=tv.get(k)
   if not tv_v:all_prereq_ok=False;break
   hv=fn(hm)
   if hv is None or hv!=tv_v:all_prereq_ok=False;break
  if not all_prereq_ok:continue
  prereq_cnt+=1
  hm_entry={'date':hm.get('MATCHDATE',''),'home':hm.get('HOMETEAMSXNAME',''),'away':hm.get('AWAYTEAMSXNAME',''),
   'result':hm.get('_computed',{}).get('match_result','')if hm.get('_computed')else'',
   'score':f'{hm.get("HOMESCORE","")}:{hm.get("AWAYSCORE","")}'}
  prereq_ml.append(hm_entry)
  # 剩余变量计数（不含先决条件），≥2才保留
  mc=0;mk=[]
  for key,fn in ext:
   if key in PREREQ_KEYS:continue
   try:
    hv=fn(hm)
    if hv is not None and tv.get(key)is not None and hv==tv[key]:mc+=1;mk.append(key)
   except:pass
  if mc<2:continue
  oe=hm.get('odds_europe',{})
  ha,hj,hh,ha2=ext_hist(hm)
  c=hm.get('_computed',{});r=c.get('match_result','')if c else''
  sh=hm.get('HOMESCORE','');sa=hm.get('AWAYSCORE','')
  entry={'date':hm.get('MATCHDATE',''),'home':hm.get('HOMETEAMSXNAME',''),'away':hm.get('AWAYTEAMSXNAME',''),'result':r,'score':f'{sh}:{sa}','mk':mk,
   'av':{'lw':ha.get('lw'),'ld':ha.get('ld'),'ll':ha.get('ll'),'dir':ha.get('dir')},
   'jc':{'lw':hj.get('lw'),'ld':hj.get('ld'),'ll':hj.get('ll'),'dir':hj.get('dir')},
   'hc':{'lw':hh.get('lw'),'ld':hh.get('ld'),'ll':hh.get('ll'),'dir':hh.get('dir'),'src':hh.get('src','')},
   'asn':{'ip':ha2.get('ip',''),'lp':ha2.get('lp',''),'lh':ha2.get('lh',''),'ll':ha2.get('ll')},
   'iwd':{'dir':_get_iw_dir_companies(oe.get('companies',[])),'odds':_get_iw_odds_companies(oe.get('companies',[]))},
   'td':{'iw_dir':tod.get('iw_dir',''),'as_pan':tod.get('as','').get('lp','') if isinstance(tod.get('as'),dict) else ''}}
  if mc not in groups:groups[mc]=[]
  groups[mc].append(entry)

 sg=sorted(groups.items(),key=lambda x:-x[0])
 rg=[]
 for cnt,ml2 in sg:
  dc=Counter()
  for e in ml2:
   for k in e['mk']:dc[k]+=1
  td=[DN[DK.index(k)]for k,c in dc.most_common()if c>=len(ml2)*0.5]
  rg.append({'cnt':cnt,'matches':ml2,'td':td})
 return{'groups':rg,'today':tv,'ht':len(ml),'hl':hist['league'],'prereq_cnt':prereq_cnt,'prereq_ml':prereq_ml}

# phone-friendly print
def pr(rs):
 now=datetime.now().strftime('%Y-%m-%d %H:%M')
 print(f'# 竞彩盘路一致性\n{now}\n')
 for rank,(m,res)in enumerate(rs,1):
  if res is None:
   print(f'{rank}. {m["home"]}vs{m["away"]} | 无缓存 | {m.get("league","")}\n')
   continue
  tv=res.get('today',{})
  cnt=res.get("groups",[])[0]["cnt"]if res.get("groups")else 0
  print(f'{"═"*60}')
  print(f'{rank}. {m["home"]} vs {m["away"]} | 3先决+{cnt}/13维 | {m.get("league","")}')
  print(f'缓存:{res.get("hl","?")}({res.get("ht",0)}场, 先决通过:{res.get("prereq_cnt",0)}场)')

  # 3先决明细
  pml=res.get('prereq_ml',[])
  if pml:
   print(f'  先决比赛({len(pml)}场):')
   for hm2 in pml:
    ri={'主胜':'✅','平局':'➖','客胜':'❌'}.get(hm2.get('result',''),'')
    sc=hm2.get('score','')
    print(f'    [{hm2.get("date","")[:10]}] {hm2.get("home","")} vs {hm2.get("away","")}  {sc}{ri}')

  # 当天明细
  print(f'  当天:')
  def today_min_lbl(w,d,l):
   """计算当天最小值标签 如 负2.20"""
   try:
    vals=[float(v)for v in[w,d,l]if v is not None and v!='-']
    if not vals:return'缺'
    idx=[float(v)if v is not None and v!='-'else 999 for v in[w,d,l]].index(min(vals))
    mn=min(vals)
    return f'{["胜","平","负"][idx]}{mn:.2f}'
   except:return'缺'
  av_lbl=today_min_lbl(tv.get('av_w'),tv.get('av_d'),tv.get('av_l'))
  jc_lbl=today_min_lbl(tv.get('jc_w'),tv.get('jc_d'),tv.get('jc_l'))
  iw_lbl=today_min_lbl(tv.get('iw_w'),tv.get('iw_d'),tv.get('iw_l'))
  print(f'    百家 {tv.get("av_dir","-")} 终:{tv.get("av_w","-")}/{tv.get("av_d","-")}/{tv.get("av_l","-")}  ←{av_lbl}')
  print(f'    竞彩 {tv.get("jc_dir","-")} 终:{tv.get("jc_w","-")}/{tv.get("jc_d","-")}/{tv.get("jc_l","-")}  ←{jc_lbl}')
  print(f'    IW   {tv.get("iw_dir","-")} 终:{tv.get("iw_w","-")}/{tv.get("iw_d","-")}/{tv.get("iw_l","-")}  ←{iw_lbl}')
  hcs=tv.get('hc_src','竞')
  print(f'    让球({hcs}):{tv.get("hc_dir","-")}  终:{tv.get("hc_w","-")}/{tv.get("hc_d","-")}/{tv.get("hc_l","-")}')
  as_ip=tv.get('as_ip','');as_lp=tv.get('as_pan','')
  print(f'    亚盘 {as_ip} → {as_lp}')
  print()

  # matched groups
  for g in res.get('groups',[]):
   cnt=g['cnt'];ms=g['matches']
   # 统计
   rc=Counter()
   for hm in ms:
    r=hm.get('result','')
    if'主胜'in r:rc['主胜']+=1
    elif'客胜'in r:rc['客胜']+=1
    elif'平'in r:rc['平局']+=1
   n=len(ms)
   stats='|'.join(f'{k}:{v}({v*100//n}%)'for k,v in sorted(rc.items()))
   print(f'  📊 {cnt}/13维 ({n}场) {stats}')
   for hm in ms:
    ri={'主胜':'✅','平局':'➖','客胜':'❌'}.get(hm.get('result',''),'')
    mk=hm.get('mk',[])
    print(f'  [{hm.get("date","")[:10]}] {hm.get("home","")} vs {hm.get("away","")}  {hm.get("score","-")} {ri}')
    av=hm.get('av',{});jc=hm.get('jc',{});hc=hm.get('hc',{});asn=hm.get('asn',{});iwd=hm.get('iwd',{})
    # 百家（有数据就显示）
    def o3(d):
     if not d:return'-/-/-'
     w=d.get('lw','-');l=d.get('ld','-');ll=d.get('ll','-')
     if w is None:return'-/-/-'
     w=float(w)if not isinstance(w,str)else-1
     l=float(l)if not isinstance(l,str)else-1
     ll=float(ll)if not isinstance(ll,str)else-1
     return f'{w:.2f}/{l:.2f}/{ll:.2f}'
    def min_lbl(d):
     if not d:return'缺'
     try:
      vals=[float(d.get(k))for k in['lw','ld','ll']if d.get(k)is not None]
      if not vals:return'缺'
      idx=[float(d.get(k,999))for k in['lw','ld','ll']].index(min(vals))
      return f'{["胜","平","负"][idx]}{min(vals):.2f}'
     except:return'缺'
    def mk_check(dim_keys):
     """检查哪些维度匹配上了"""
     return''# 只显示方向箭头和数值，✓标记去掉以保持干净
    ad=av.get('dir','-')
    print(f'    百家 {ad} 终:{o3(av)}  ←{min_lbl(av)}')
    jd=jc.get('dir','-')
    print(f'    竞彩 {jd} 终:{o3(jc)}  ←{min_lbl(jc)}')
    iw_odds=iwd.get('odds',{})
    if iw_odds:
     iwd_dir=iwd.get('dir','-')
     print(f'    IW   {iwd_dir} 终:{o3(iw_odds)}  ←{min_lbl(iw_odds)}')
    hc_src=hc.get('src','竞')
    hcd=hc.get('dir','-')
    print(f'    让球({hc_src}):{hcd}  终:{o3(hc)}')
    as_ip=asn.get('ip','-').replace('↑','').replace('↓','').replace(' ','').strip()
    as_lp=asn.get('lp','-').replace('↑','').replace('↓','').replace(' ','').strip()
    if as_ip and as_ip!='-':
     print(f'    亚盘 {as_ip} → {as_lp}')
    print()
  print()

if __name__=='__main__':
 ds=sys.argv[1]if len(sys.argv)>1 else None
 ml,dt=get_ms(ds)
 if ml:
  print('\n[采集]...')
  for m in ml:
   fid=m.get('fid','')
   if not fid:continue
   print(f'  {m["matchnum"]}...',end=' ')
   m['odds']=fo(fid);print('OK')
   time.sleep(0.3)
  print('\n[搜索]...')
  rs=[]
  for m in ml:
   lg=m.get('league','')
   print(f'  {m["matchnum"]}{lg}...',end=' ')
   h=ld(lg)
   if not h:print('无缓存');rs.append((m,None));continue
   print(f'{h["total"]}场')
   rs.append((m,sr(h,m.get('odds',{}))))
  rs.sort(key=lambda x:-(x[1].get('groups',[])[0]['cnt']if x[1]and x[1].get('groups')else 0))
  pr(rs)
