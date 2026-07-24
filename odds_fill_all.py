# -*- coding: utf-8 -*-
"""
全量补全反馈数据的赔率特征
- 从报告 .md 文件提取竞彩/IW/百家欧赔
- 从 step4 提取让球指数
- 从 step6 提取亚盘数据
- 覆盖所有缺失条目
"""
import os, sys, json, re
from datetime import datetime as dt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

# 星期映射
WEEKDAYS = ['周一','周二','周三','周四','周五','周六','周日']

# ===== 正则 =====
# 欧赔表: 竞彩/IW/百家三行
EURO_TABLE_RE = re.compile(
    r'\|\s*(竞彩官方|Interwetten|百家平均)\s*'
    r'\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*'
    r'\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
)

# 让球表 step4: | 公司 | 让球 | 初盘胜 | 初盘平 | 初盘负 | 即时胜 | 即时平 | 即时负 |
HANDICAP_TABLE_RE = re.compile(
    r'\|\s*([^|]+)\s*\|\s*'        # 公司
    r'([+-]?\d+(?:[./]\d+)?)\s*\|\s*'  # 让球数
    r'([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*'
    r'\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
)

# 亚盘表 step6: | 公司 | 初盘 | 即时盘 |
# 初盘格式: "半球 0.800|0.910"
ASIAN_TABLE_RE = re.compile(
    r'\|\s*([^|]+)\s*\|\s*'        # 公司
    r'([^|]+?)\s*\|\s*'            # 初盘 (盘口 水位主|水位客)
    r'([^|]+?)\s*\|'                # 即时盘
)

# 澳门亚盘（报告头部）
MACAU_LINE_RE = re.compile(r'🔗\s*澳门亚盘[：:]\s*(.+)')

# 让球数（报告头部） 
HANDICAP_LINE_RE = re.compile(r'让球[：:]\s*(主队)?([+-]?\d+(?:[./]\d+)?)')


def get_report_for(date, match_num):
    """找到对应比赛的报告文件"""
    dpath = os.path.join(TASKS_DIR, date)
    if not os.path.exists(dpath):
        return None
    
    # 尝试找报告 .md 文件
    # 文件名格式: 周X001_xxx.md
    for f in os.listdir(dpath):
        if not f.endswith('.md') or f.startswith('README'):
            continue
        m = re.match(r'(周[一二三四五六日]\d+)_', f)
        if m:
            mn_full = m.group(1)  # e.g. "周五001"
            mn_num = m.group(1)[3:]  # e.g. "001"
            if mn_num == match_num or mn_full == match_num or mn_full.endswith(match_num):
                return os.path.join(dpath, f)
        # 也匹配纯数字
        if re.match(r'^' + re.escape(match_num) + r'_', f):
            return os.path.join(dpath, f)
    
    # 用星期前缀再试一次
    try:
        wd = dt.strptime(date, '%Y-%m-%d').weekday()
        wd_name = WEEKDAYS[wd]
        for f in os.listdir(dpath):
            if f.startswith(wd_name + match_num + '_') and f.endswith('.md'):
                return os.path.join(dpath, f)
    except:
        pass
    
    return None


def find_step_file(date, match_num, group, filename):
    """在 match 目录下找步骤文件"""
    dpath = os.path.join(TASKS_DIR, date)
    if not os.path.exists(dpath):
        return None
    
    for base in [dpath, os.path.join(dpath, 'data')]:
        if not os.path.exists(base):
            continue
        for sub in os.listdir(base):
            sp = os.path.join(base, sub)
            if not os.path.isdir(sp) or not sub.startswith('match'):
                continue
            # 检查 meta.json 确认 match_num
            meta_f = os.path.join(sp, 'meta.json')
            if not os.path.exists(meta_f):
                continue
            try:
                meta = json.load(open(meta_f, 'r', encoding='utf-8'))
                meta_mn = meta.get('matchnum', '')
                if not (meta_mn == match_num or meta_mn.endswith(match_num)):
                    continue
            except:
                continue
            fpath = os.path.join(sp, group, filename)
            if os.path.exists(fpath):
                return fpath
    return None


def extract_odds_from_report(content):
    """从报告文件提取所有赔率数据"""
    result = {}
    
    # 1. 欧赔表（竞彩/IW/百家）
    for m in EURO_TABLE_RE.finditer(content):
        company = m.group(1)
        prefix = {
            '竞彩官方': '欧赔',
            'Interwetten': 'IW',
            '百家平均': '百家',
        }.get(company, company)
        
        result[f'{prefix}初胜'] = float(m.group(2))
        result[f'{prefix}初平'] = float(m.group(3))
        result[f'{prefix}初负'] = float(m.group(4))
        result[f'{prefix}即胜'] = float(m.group(5))
        result[f'{prefix}即平'] = float(m.group(6))
        result[f'{prefix}即负'] = float(m.group(7))
    
    # 2. 澳门亚盘
    m = MACAU_LINE_RE.search(content)
    if m:
        result['澳门亚盘'] = m.group(1).strip()
    
    # 3. 让球数
    m = HANDICAP_LINE_RE.search(content)
    if m:
        result['让球数'] = m.group(2).strip()
    
    return result


def extract_handicap_from_step4(content):
    """从 step4 提取让球指数"""
    result = {}
    for m in HANDICAP_TABLE_RE.finditer(content):
        company = m.group(1).strip()
        rq = m.group(2).strip()
        cs, cp, cf = m.group(3), m.group(4), m.group(5)
        js, jp, jf = m.group(6), m.group(7), m.group(8)
        
        # 只存竞彩让球（主要数据）
        if '竞彩' in company:
            result['让球数'] = rq
            result['让球初胜'] = float(cs)
            result['让球初平'] = float(cp)
            result['让球初负'] = float(cf)
            result['让球即胜'] = float(js)
            result['让球即平'] = float(jp)
            result['让球即负'] = float(jf)
    
    return result


def extract_asian_from_step6(content):
    """从 step6 提取亚盘数据"""
    result = {}
    for m in ASIAN_TABLE_RE.finditer(content):
        company = m.group(1).strip()
        initial = m.group(2).strip()
        current = m.group(3).strip()
        
        if '澳门' in company:
            result['澳门初盘'] = initial
            result['澳门即时盘'] = current
            # 解析盘口
            pan_re = re.match(r'([^\d]+)', initial)
            if pan_re:
                result['澳门亚盘'] = pan_re.group(1).strip()
    
    return result


def main():
    print(f'{"="*60}')
    print(f'全量赔率特征补全')
    print(f'{"="*60}\n')
    
    # 加载反馈
    raw = open(FEEDBACK_FILE, 'r', encoding='utf-8').read()
    fb = json.loads(raw)
    dates = fb.get('dates', {})
    
    print(f'[1/4] 加载反馈数据: {len(dates)} 个日期')
    
    # 统计
    total = 0
    has_full_odds = 0  # 有竞彩+IW+百家
    partial = 0        # 只有部分
    no_odds = 0        # 完全没有
    
    # 新补的计数
    filled_euro = 0
    filled_iw = 0
    filled_baijia = 0
    filled_handicap = 0
    filled_asian = 0
    skipped = 0
    
    for date in sorted(dates.keys()):
        items = dates[date].get('feedback', []) if isinstance(dates[date], dict) else dates[date]
        
        for item in items:
            c = item.get('combos', {})
            if not isinstance(c, dict):
                item['combos'] = c = {}
            
            mn = item.get('match_num', '')
            if not mn:
                skipped += 1
                continue
            
            total += 1
            has_euro = c.get('欧赔初胜') is not None
            
            # 已有 IW/百家?
            has_iw = c.get('IW初胜') is not None
            has_baijia = c.get('百家初胜') is not None
            has_handicap = c.get('让球初胜') is not None
            has_asian = c.get('澳门亚盘') is not None or c.get('澳门初盘') is not None
            
            if has_euro and has_iw and has_baijia:
                has_full_odds += 1
            elif has_euro or has_iw or has_baijia:
                partial += 1
            else:
                no_odds += 1
            
            # 如果三门齐全并且亚盘让球也有，跳过
            if has_euro and has_iw and has_baijia and has_handicap and has_asian:
                continue
            
            # === 从报告提取 ===
            report_path = get_report_for(date, mn)
            if report_path:
                content = open(report_path, 'r', encoding='utf-8').read()
                odds = extract_odds_from_report(content)
                
                if '欧赔初胜' in odds and not has_euro:
                    c['欧赔初胜'] = odds['欧赔初胜']
                    c['欧赔初平'] = odds['欧赔初平']
                    c['欧赔初负'] = odds['欧赔初负']
                    c['欧赔即胜'] = odds['欧赔即胜']
                    c['欧赔即平'] = odds['欧赔即平']
                    c['欧赔即负'] = odds['欧赔即负']
                    filled_euro += 1
                
                if 'IW初胜' in odds and not has_iw:
                    c['IW初胜'] = odds['IW初胜']
                    c['IW初平'] = odds['IW初平']
                    c['IW初负'] = odds['IW初负']
                    c['IW即胜'] = odds['IW即胜']
                    c['IW即平'] = odds['IW即平']
                    c['IW即负'] = odds['IW即负']
                    filled_iw += 1
                
                if '百家初胜' in odds and not has_baijia:
                    c['百家初胜'] = odds['百家初胜']
                    c['百家初平'] = odds['百家初平']
                    c['百家初负'] = odds['百家初负']
                    c['百家即胜'] = odds['百家即胜']
                    c['百家即平'] = odds['百家即平']
                    c['百家即负'] = odds['百家即负']
                    filled_baijia += 1
                
                # 亚盘（报告头部也有）
                if '澳门亚盘' in odds and not has_asian:
                    c['澳门亚盘'] = odds['澳门亚盘']
                    filled_asian += 1
            
            # === 从步骤文件补让球指数 ===
            if not has_handicap:
                step4 = find_step_file(date, mn, 'group02_handicap', 'step4_handicap_base.txt')
                if step4:
                    content = open(step4, 'r', encoding='utf-8').read()
                    hc = extract_handicap_from_step4(content)
                    if hc:
                        for k, v in hc.items():
                            c[k] = v
                        filled_handicap += 1
            
            # === 从步骤文件补亚盘 ===
            if not has_asian:
                step6 = find_step_file(date, mn, 'group03_asian', 'step6_asian_base.txt')
                if step6:
                    content = open(step6, 'r', encoding='utf-8').read()
                    ac = extract_asian_from_step6(content)
                    if ac:
                        for k, v in ac.items():
                            c[k] = v
                        filled_asian += 1
    
    # 保存
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(fb, f, ensure_ascii=False, indent=2)
    
    print(f'\n[2/4] 补全结果:')
    print(f'  竞彩欧赔: {filled_euro} 场')
    print(f'  IW欧赔:   {filled_iw} 场')
    print(f'  百家欧赔: {filled_baijia} 场')
    print(f'  让球指数: {filled_handicap} 场')
    print(f'  亚盘数据: {filled_asian} 场')
    
    # 统计最终状态
    print(f'\n[3/4] 最终状态:')
    final_has = {'竞彩':0, 'IW':0, '百家':0, '让球':0, '亚盘':0}
    for date, v in dates.items():
        for item in v.get('feedback', []):
            c = item.get('combos', {})
            if not isinstance(c, dict): continue
            if c.get('欧赔初胜'): final_has['竞彩'] += 1
            if c.get('IW初胜'): final_has['IW'] += 1
            if c.get('百家初胜'): final_has['百家'] += 1
            if c.get('让球初胜'): final_has['让球'] += 1
            if c.get('澳门初盘') or c.get('澳门亚盘'): final_has['亚盘'] += 1
    
    for k, v in final_has.items():
        print(f'  {k}: {v}/{total} ({v*100//total}%)')
    
    print(f'\n[4/4] 保存完成: {FEEDBACK_FILE}')


if __name__ == '__main__':
    main()
