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
 try:
  url=f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
  x=sess.get(url,timeout=10);x.encoding='gbk'
  s=BeautifulSoup(x.text,'html.parser')
  for t in s.find_all('table'):
   for tr in t.find_all('tr'):
    td=tr.find_all('td')
    if len(td)<12:continue
    t0=td[0].get_text().strip()
    if not t0.isdigit():continue
    n=int(t0)
    if n not in(1,2,3):continue
    nm=td[1].get_text().strip()
    ip=td[4].get_text().strip().replace(chr(160),'')
    lp=td[10].get_text().strip().replace(chr(160),'')
    try:
     ih=float(re.search(r'([\d.]+)',td[3].get_text()).group(1))
     il=float(re.search(r'([\d.]+)',td[5].get_text()).group(1))
     lh=float(re.search(r'([\d.]+)',td[9].get_text()).group(1))
     ll=float(re.search(r'([\d.]+)',td[11].get_text()).group(1))
    except:ih=il=lh=ll=''
    e={'name':nm,'ip':ip,'ih':ih,'il':il,'lp':lp,'lh':lh,'ll':ll}
    if'澳门'in nm or n==1:
     if not r['as']or'澳门'in nm:r['as']=e
 except:pass
 return r

def ld(league):
 cp=None;best=0;lk=''
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
    if ml_cnt>best%1000:score+=ml_cnt*0.001  # 场数多也加分
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
   if'澳门'in item.get('name','')or item==oa[0]:
    asn={'lp':item.get('live_pan',''),'lh':item.get('lh',''),'ll':item.get('ll','')};break
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
 tv['av_dir']=av.get('dir','');tv['iw_dir']=tod.get('iw_dir','');tv['as_pan']=asn.get('lp','')
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
  ('as_pan',lambda hm:next((item.get('live_pan')for item in(hm.get('odds_asian',[])or[])if'澳门'in item.get('name','')or item==(hm.get('odds_asian',[])or[{}])[0]),None)),
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

 groups={}
 for hm in ml:
  # 先决条件：澳门亚盘(受/非受二值) + 百家盘路(精确) + IW盘路(⬆/⬇精确,➡通配)
  all_prereq_ok=True
  for k in PREREQ_KEYS:
   idx=DK.index(k)
   key,fn=ext[idx]
   tv_v=tv.get(k)
   if not tv_v:all_prereq_ok=False;break
   hv=fn(hm)
   if hv is None:all_prereq_ok=False;break
   if k=='as_pan':
    # 亚盘：只检查受/非受
    if tv_v.startswith('受')!=hv.startswith('受'):all_prereq_ok=False;break
   elif k=='iw_dir':
    # IW方向：➡通配（当天➡的位置可匹配历史的任何值）
    ok=True
    for a,b in zip(tv_v,hv):
     if a!='➡' and a!=b:ok=False;break
    if not ok:all_prereq_ok=False;break
   else:
    # 百家盘路：精确匹配
    if hv!=tv_v:all_prereq_ok=False;break
  if not all_prereq_ok:continue
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
   'asn':{'lp':ha2.get('lp'),'lh':ha2.get('lh'),'ll':ha2.get('ll')},
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
 return{'groups':rg,'today':tv,'ht':len(ml),'hl':hist['league']}

# phone-friendly print
def pr(rs):
 now=datetime.now().strftime('%Y-%m-%d %H:%M')
 print(f'# 竞彩盘路一致性\n{now}\n')
 for rank,(m,res)in enumerate(rs,1):
  if res is None:
   print(f'**{rank}. {m["home"]}vs{m["away"]}** | 无缓存 | {m.get("league","")}\n')
   continue
  tv=res.get('today',{})
  print(f'**{rank}. {m["home"]}vs{m["away"]}** | 3先决+{res.get("groups",[])[0]["cnt"] if res.get("groups") else 0}/13剩余 | {m.get("league","")}')
  print(f'缓存:{res.get("hl","?")}({res.get("ht",0)}场)')
  print()
  # today dimensions
  print('📋当天:')
  print(f'  盘路: 百{tv.get("av_dir","-")} | IW{tv.get("iw_dir","-")} | 让{tv.get("hc_dir","-")}')
  print(f'  澳门: {tv.get("as_pan","-")}')
  avw=tv.get('av_w','-');avd=tv.get('av_d','-');avl=tv.get('av_l','-')
  print(f'  百家: {avw}/{avd}/{avl}')
  jcw=tv.get('jc_w','-');jcd=tv.get('jc_d','-');jcl=tv.get('jc_l','-')
  print(f'  竞彩: {jcw}/{jcd}/{jcl}')
  hcw=tv.get('hc_w','-');hcd=tv.get('hc_d','-');hcl=tv.get('hc_l','-');hcs=tv.get('hc_src','')
  print(f'  让球({hcs}): {hcw}/{hcd}/{hcl}')
  iww=tv.get('iw_w','-');iwd=tv.get('iw_d','-');iwl=tv.get('iw_l','-')
  print(f'  IW赔率: {iww}/{iwd}/{iwl}')
  print()
  # matched groups
  for g in res.get('groups',[]):
   cnt=g['cnt'];ms=g['matches'];td=g['td']
   print(f'📅 {cnt}/13维 ({len(ms)}场)')
   for hm in ms:
    ri={'主胜':'✅','平局':'➖','客胜':'❌'}.get(hm.get('result',''),'')
    dt=hm.get('date','');hmn=hm.get('home','');awn=hm.get('away','')
    sc=hm.get('score','')
    print(f'  {hmn}vs{awn} {sc}{ri} ({dt})')
    # per-dimension lines
    mk=hm.get('mk',[])
    av=hm.get('av',{});jc=hm.get('jc',{});hc=hm.get('hc',{});asn=hm.get('asn',{});iwd=hm.get('iwd',{});td=hm.get('td',{})
    # direction line
    def nz(v,d='-'):return d if v is None else str(v)
    ad=nz(av.get('dir'));id_=nz(iwd.get('dir'));hd=nz(hc.get('dir'))
    print(f'    盘路: 百{ad}✓ | IW{id_}✓ | 让{hd}{"✓" if "hc_dir" in mk else ""}')
    # asian pan
    ap=nz(asn.get('lp'))
    print(f'    澳门: {ap}✓')
    # av values
    def vv(d,k):
     v=d.get(k)
     if v is None:return'-'
     return f'{v:.2f}'if isinstance(v,float)else str(v)
    aw=vv(av,'lw');ad2=vv(av,'ld');al=vv(av,'ll')
    awm='✓'if'av_w'in mk else'';adm='✓'if'av_d'in mk else'';alm='✓'if'av_l'in mk else''
    print(f'    百家: {aw}{awm}/{ad2}{adm}/{al}{alm}')
    jw=vv(jc,'lw');jd2=vv(jc,'ld');jl=vv(jc,'ll')
    jwm='✓'if'jc_w'in mk else'';jdm='✓'if'jc_d'in mk else'';jlm='✓'if'jc_l'in mk else''
    print(f'    竞彩: {jw}{jwm}/{jd2}{jdm}/{jl}{jlm}')
    # IW终赔
    iw_odds=iwd.get('odds',{})
    if iw_odds:
     iww=vv(iw_odds,'lw');iwd2=vv(iw_odds,'ld');iwl=vv(iw_odds,'ll')
     iwm='✓'if'iw_w'in mk else'';iwdm='✓'if'iw_d'in mk else'';iwlm='✓'if'iw_l'in mk else''
     print(f'    IW赔率: {iww}{iwm}/{iwd2}{iwdm}/{iwl}{iwlm}')
    hw=vv(hc,'lw');hd2=vv(hc,'ld');hl=vv(hc,'ll')
    hwm='✓'if'hc_w'in mk else'';hdm='✓'if'hc_d'in mk else'';hlm='✓'if'hc_l'in mk else''
    hcs=hc.get('src','')
    print(f'    让球({hcs}): {hw}{hwm}/{hd2}{hdm}/{hl}{hlm}')
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
