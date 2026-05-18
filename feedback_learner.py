# -*- coding: utf-8 -*-
"""
竞彩反馈学习引擎 V2 - 组合模式 + Step25/26数据 + 自动修正

功能：
1. 从 feedback.json 提取组合特征（欧赔趋势×让球趋势×亚盘趋势×百家趋势×盘路匹配）
2. 从 step25_zhuangjia.json 提取庄家盈亏方向数据
3. 从 step26_profit_ratio.json 提取盈亏比例数据
4. 按联赛/信心度/组合/庄家方向 统计准确率
5. 生成 learned_patterns_v2.json（供 final_conclusion_generator.py 使用）
6. 自动修正信心值：基于历史准确率调整未来预测的信心值

触发方式：
- 手动：python jingcai/feedback_learner.py
- 自动：run_pipeline.py 末尾自动调用
"""
import os, sys, json, re, glob
from datetime import datetime

# Import expert pattern engine (for expert pattern collection)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from expert_pattern_engine import ExpertPatternEngine
    HAS_EXPERT_ENGINE = True
except ImportError:
    HAS_EXPERT_ENGINE = False

# Fix encoding for Windows console
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
LEARNED_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'learned_patterns_v2.json')
SCORES_HISTORY = os.path.join(SCRIPT_DIR, 'learnings', 'scores_history.json')
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')


from _util import rd, safe_json_load, ensure_utf8_stdout
ensure_utf8_stdout()


def extract_combo_from_report(report_content):
    """从最终报告提取组合特征（包含精细模式）"""
    combo = {}
    
    # ===== 1. 澳门亚盘（具体盘口）=====
    # 报告头部: 🔗 澳门亚盘: 半球
    m = re.search(r'澳门亚盘[：:](.+)', report_content)
    if m:
        asian_line = m.group(1).strip()
        if asian_line != '未知':
            combo['澳门亚盘'] = asian_line
    
    # Step6: 澳门初盘/即时盘（如果报告头部没有澳门亚盘数据）
    # 例: | 澳门 | 半球 1.040|0.800 | 半球/一球 升 1.000|0.840 |
    m = re.search(r'\|\s*澳门\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', report_content)
    if m:
        combo['澳门初盘'] = m.group(1).strip()
        combo['澳门即时盘'] = m.group(2).strip()
        # 从初盘提取盘口（如 "半球 1.040|0.800" → "半球"）
        if not combo.get('澳门亚盘'):
            pan_kou_m = re.match(r'([^( |\d)]+)', m.group(1).strip())
            if pan_kou_m:
                combo['澳门亚盘'] = pan_kou_m.group(1).strip()
    
    # ===== 2. 欧赔盘路变化（竞彩/IW/百家）=====
    # 报告头部欧赔表: | 竞彩官方 | 1.76 | 3.30 | 3.88 | 1.63 | 3.45 | 4.42 | ⬇⬆⬆ |
    oupei_pattern = r'\|\s*(竞彩官方|Interwetten|百家平均)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([⬇⬆⬉⬊➡→]+)\s*\|'
    for m in re.finditer(oupei_pattern, report_content):
        company = m.group(1)
        change = m.group(8).strip()
        # 转换箭头为文字
        change_text = change.replace('⬇', '降').replace('⬆', '升').replace('➡', '不变').replace('→', '不变').replace('⬉', '升').replace('⬊', '降')
        if company == '竞彩官方':
            combo['竞彩欧赔盘路'] = change_text
        elif company == 'Interwetten':
            combo['IW欧赔盘路'] = change_text
        elif company == '百家平均':
            combo['百家欧赔盘路'] = change_text
    
    # Step24 盘路基准表: | 竞彩欧赔 | ⬇⬆⬆ |
    panlu_pattern = r'\|\s*(竞彩欧赔|Interwetten|百家平均|让球指数)\s*\|\s*([⬇⬆⬉⬊➡→]+)\s*\|'
    for m in re.finditer(panlu_pattern, report_content):
        company = m.group(1)
        change = m.group(2).strip()
        change_text = change.replace('⬇', '降').replace('⬆', '升').replace('➡', '不变').replace('→', '不变').replace('⬉', '升').replace('⬊', '降')
        if company == '竞彩欧赔':
            combo['竞彩欧赔盘路_基准'] = change_text
        elif company == 'Interwetten':
            combo['IW欧赔盘路_基准'] = change_text
        elif company == '百家平均':
            combo['百家欧赔盘路_基准'] = change_text
        elif company == '让球指数':
            combo['让球盘路_基准'] = change_text
    
    # ===== 3. 让球盘路（Step5让球同赔）=====
    # 格式: | ↓↑↑ | 高 |
    rq_panlu = re.findall(r'\|\s*([↓↑→]+)\s*\|\s*(高|中|低)\s*\|', report_content)
    if rq_panlu:
        combo['让球同赔盘路样本'] = len(rq_panlu)
    
    # ===== 4. 澳门亚盘同赔盘路（Step7）=====
    # 格式: 盘口不变 降水, 升盘 降水, 降盘 降水, 盘口不变 升水, 盘口不变 水位不变, 升盘 升水
    macau_panlu_types = re.findall(r'盘口不变\s*(?:降水|升水|水位不变)|升盘\s*(?:降水|升水)|降盘\s*(?:降水|升水)', report_content)
    if macau_panlu_types:
        combo['澳门亚盘同赔样本'] = len(macau_panlu_types)
        # 统计各类型
        panlu_counts = {}
        for pt in macau_panlu_types:
            panlu_counts[pt] = panlu_counts.get(pt, 0) + 1
        combo['澳门亚盘同赔分布'] = panlu_counts
    
    # ===== 5. 各维度信号（从"各维度信号明细"表格）=====
    # 格式: | 维度 | 分值 方向 | 权重 |
    # 例: | 欧赔趋势 | -0.700 利好客 | 10% |
    #     | 竞彩同赔 | -1.000 利好客 | 12% |
    #     | 澳门亚盘 | +0.036 利好主 | 10% |
    #     | 客队客场 | +0.000 中立 | 12% |
    dim_pattern = r'\|\s*(欧赔趋势|竞彩同赔|IW同赔|澳门亚盘|让球同赔|主队主场|客队客场|百家对比|庄家盈亏|盘路匹配)\s*\|\s*([+-]?\d+\.\d+)\s+(利好主|利好客|中立)\s*\|\s*(\d+)%'
    
    # 维度名称映射（报告中的名称 → 内部名称）
    dim_map = {
        '欧赔趋势': '欧赔趋势',
        '竞彩同赔': '欧赔趋势',
        'IW同赔': '欧赔趋势',
        '澳门亚盘': '亚盘趋势',
        '让球同赔': '让球趋势',
        '主队主场': '主队主场',
        '客队客场': '客队客场',
        '百家对比': '百家对比',
        '庄家盈亏': '庄家盈亏',
        '盘路匹配': '盘路匹配',
    }
    
    for m in re.finditer(dim_pattern, report_content):
        dim_name = m.group(1)
        score = float(m.group(2))
        direction = m.group(3)
        weight = int(m.group(4))
        
        # 映射到内部维度名
        internal_dim = dim_map.get(dim_name, dim_name)
        combo[f'{internal_dim}_score'] = score
        combo[f'{internal_dim}_dir'] = direction
        combo[f'{internal_dim}_weight'] = weight
        
        # 盘路匹配同时存入combo['盘路匹配']供panlu_stats统计
        if internal_dim == '盘路匹配':
            combo['盘路匹配'] = direction
        
        # 根据方向推断百分比
        if direction == '利好主' and score > 0:
            combo[f'{internal_dim}_pct'] = 60 + int(abs(score) * 20)
        elif direction == '利好客' and score < 0:
            combo[f'{internal_dim}_pct'] = 60 + int(abs(score) * 20)
        else:
            combo[f'{internal_dim}_pct'] = 50
    
    # 补充提取让球趋势（从Step5让球同赔数据）
    # 如果上面没提取到让球趋势_dir，尝试从Step5数据推断
    if '让球趋势_dir' not in combo:
        rq_panlu = combo.get('让球盘路_基准', '')
        if rq_panlu:
            if '降升升' in rq_panlu or '降升' in rq_panlu:
                combo['让球趋势_dir'] = '利好客'
                combo['让球趋势_score'] = -0.3
                combo['让球趋势_weight'] = 10
                combo['让球趋势_pct'] = 60
            elif '升降降' in rq_panlu or '升降' in rq_panlu:
                combo['让球趋势_dir'] = '利好主'
                combo['让球趋势_score'] = 0.3
                combo['让球趋势_weight'] = 10
                combo['让球趋势_pct'] = 60
            else:
                combo['让球趋势_dir'] = '中立'
                combo['让球趋势_score'] = 0.0
                combo['让球趋势_weight'] = 10
                combo['让球趋势_pct'] = 50
    
    # ===== 6. 提取盘路匹配度评分（高/中/低）=====
    panlu_match = re.search(r'盘路匹配度评分[：:](高|中|低)', report_content)
    if panlu_match:
        combo['盘路匹配'] = panlu_match.group(1)
    if '盘路匹配' not in combo:
        panlu_stat = re.search(r'盘路匹配统计[：:]?(\d+)场.*?胜(\d+).*?平(\d+).*?负(\d+)', report_content)
        if panlu_stat:
            total = int(panlu_stat.group(1))
            wins = int(panlu_stat.group(2))
            if total >= 5 and wins / total >= 0.6:
                combo['盘路匹配'] = '高'
            elif total >= 3 and wins / total >= 0.4:
                combo['盘路匹配'] = '中'
            elif total >= 3:
                combo['盘路匹配'] = '低'
    
    # ===== 7. 提取欧赔数值（供专家模式引擎使用）=====
    oupei_vals = re.search(r'竞彩官方\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', report_content)
    if oupei_vals:
        combo['欧赔初胜'] = float(oupei_vals.group(1))
        combo['欧赔初平'] = float(oupei_vals.group(2))
        combo['欧赔初负'] = float(oupei_vals.group(3))
        combo['欧赔即胜'] = float(oupei_vals.group(4))
        combo['欧赔即平'] = float(oupei_vals.group(5))
        combo['欧赔即负'] = float(oupei_vals.group(6))
    
    # ===== 8. 提取澳门亚盘数值（供专家模式引擎使用）=====
    macau_vals = re.search(r'\|\s*澳门\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', report_content)
    if macau_vals:
        combo['澳门初盘'] = macau_vals.group(1).strip()
        combo['澳门即时盘'] = macau_vals.group(2).strip()
    
    # ===== 9. 提取综合信心和竞彩预测（从最终结论）=====
    m = re.search(r'综合信心[:\s]*(\d+)%', report_content)
    if m:
        combo['confidence'] = int(m.group(1))
    
    # 竞彩预测
    m = re.search(r'\*\*竞彩预测\*\*\s*\|\s*([^（|]+)', report_content)
    if m:
        combo['prediction'] = m.group(1).strip()
    
    # 信心值（从最终结论表格）
    m = re.search(r'\*\*信心\*\*\s*\|\s*(\d+)%', report_content)
    if m and 'confidence' not in combo:
        combo['confidence'] = int(m.group(1))
    
    return combo


def extract_step25_data(match_dir, date_dir):
    """从 step25_zhuangjia.json 提取庄家盈亏方向"""
    s25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
    
    # 如果直接路径不存在，尝试在 data/match* 子目录中查找
    if not os.path.exists(s25_file):
        if date_dir:
            data_dir = os.path.join(TASKS_DIR, date_dir, 'data')
        else:
            data_dir = os.path.join(os.path.dirname(match_dir), 'data')
        if os.path.exists(data_dir):
            for sub in os.listdir(data_dir):
                sub_path = os.path.join(data_dir, sub)
                if os.path.isdir(sub_path):
                    candidate = os.path.join(sub_path, 'step25_zhuangjia.json')
                    if os.path.exists(candidate):
                        s25_file = candidate
                        break
    
    if not os.path.exists(s25_file):
        return {}
    
    try:
        s25 = json.loads(rd(s25_file))
    except:
        return {}
    
    result = {}
    data = s25.get('data', s25)
    
    # 庄家盈亏方向
    for key in ['主胜', '平局', '客胜']:
        if key in data:
            item = data[key]
            result[f'{key}_盈亏'] = item.get('盈亏方向', '')
            result[f'{key}_投注额'] = item.get('投注额', '')
            result[f'{key}_占比'] = item.get('占比', '')
    
    # 综合方向
    result['庄家方向'] = s25.get('conclusion', {}).get('庄家方向', '')
    result['大热方'] = s25.get('conclusion', {}).get('大热方', '')
    
    # 盈亏方向（从 labels 推断）
    labels = s25.get('labels', {})
    if not result['庄家方向']:
        for key in ['主胜', '平局', '客胜']:
            if key in labels:
                profit_val = labels[key].get('profit', '')
                if profit_val in ['赢钱', '少', '中']:
                    result['庄家方向'] = key
                    break
    
    if result.get('庄家方向'):
        result['盈亏方向'] = result['庄家方向']
    
    # 大热方
    if result.get('大热方'):
        result['投注大热'] = result['大热方']
    
    return result


def extract_step26_data(match_dir, date_dir):
    """从 step26_profit_ratio.json 提取盈亏比例"""
    s26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
    
    # 如果直接路径不存在，尝试在 data/match* 子目录中查找
    if not os.path.exists(s26_file):
        if date_dir:
            data_dir = os.path.join(TASKS_DIR, date_dir, 'data')
        else:
            data_dir = os.path.join(os.path.dirname(match_dir), 'data')
        if os.path.exists(data_dir):
            for sub in os.listdir(data_dir):
                sub_path = os.path.join(data_dir, sub)
                if os.path.isdir(sub_path):
                    candidate = os.path.join(sub_path, 'step26_profit_ratio.json')
                    if os.path.exists(candidate):
                        s26_file = candidate
                        break
    
    if not os.path.exists(s26_file):
        return {}
    
    try:
        s26 = json.loads(rd(s26_file))
    except:
        return {}
    
    result = {}
    data = s26.get('data', s26)
    
    for key in ['主胜', '平局', '客胜']:
        if key in data:
            item = data[key]
            result[f'{key}_盈亏比'] = item.get('盈亏比例', 0)
            result[f'{key}_盈亏方向'] = item.get('方向', '')
    
    # 从 analysis 提取
    analysis = s26.get('analysis', {})
    
    # 庄家胜/平/负盈亏（赢钱/亏钱）
    for key in ['庄家胜盈亏', '庄家平盈亏', '庄家负盈亏']:
        val = analysis.get(key, '')
        result[key] = val
        if '赢' in val:
            result[f'{key}_方向'] = '正'
        elif '亏' in val:
            result[f'{key}_方向'] = '负'
    
    # 盈亏方向（庄主胜盈/庄平盈/庄客盈）
    for key in ['庄主胜盈', '庄平盈', '庄客盈']:
        if key in analysis:
            result[f'{key}_方向'] = analysis[key]
    
    # 投注占比
    bet_ratio = analysis.get('投注占比', {})
    if bet_ratio:
        result['投注占比_主'] = bet_ratio.get('胜', bet_ratio.get('主', ''))
        result['投注占比_平'] = bet_ratio.get('平', '')
        result['投注占比_客'] = bet_ratio.get('负', bet_ratio.get('客', ''))
    
    # 盈亏占比
    profit_ratio = analysis.get('盈亏占比', {})
    if profit_ratio:
        result['盈亏占比_主'] = profit_ratio.get('胜', profit_ratio.get('主', ''))
        result['盈亏占比_平'] = profit_ratio.get('平', '')
        result['盈亏占比_客'] = profit_ratio.get('负', profit_ratio.get('客', ''))
    
    # 综合盈亏方向
    if analysis.get('庄家最看好'):
        result['综合盈亏方向'] = analysis['庄家最看好']
    
    return result


def build_match_map():
    """构建 matchnum → 文件路径 的映射"""
    match_map = {}
    if not os.path.exists(TASKS_DIR):
        return match_map
    
    for date in sorted(os.listdir(TASKS_DIR)):
        date_dir = os.path.join(TASKS_DIR, date)
        if not os.path.isdir(date_dir):
            continue
        
        # 扫描最终报告
        for f in glob.glob(os.path.join(date_dir, '周*.md')):
            m = re.match(r'(周[一二三四五六日]\d+)[_]', os.path.basename(f))
            if m:
                match_num = m.group(1)
                match_map[match_num] = {
                    'report': f,
                    'date': date,
                    'dir': os.path.dirname(f),
                }
        
        # 扫描 data/match* 目录
        data_dir = os.path.join(date_dir, 'data')
        if os.path.exists(data_dir):
            for md in os.listdir(data_dir):
                md_path = os.path.join(data_dir, md)
                if not os.path.isdir(md_path) or not md.startswith('match'):
                    continue
                meta_file = os.path.join(md_path, 'meta.json')
                if os.path.exists(meta_file):
                    try:
                        meta = json.loads(rd(meta_file))
                        mn = meta.get('matchnum', '')
                        if mn:
                            # 如果已有条目（来自md报告），保留report路径
                            if mn in match_map and match_map[mn].get('report'):
                                match_map[mn]['dir'] = md_path
                                match_map[mn]['meta'] = meta
                            else:
                                match_map[mn] = {
                                    'report': '',
                                    'date': date,
                                    'dir': md_path,
                                    'meta': meta,
                                }
                    except:

                        log.warn(f"[learn] 解析异常")
    # 添加别名映射：md报告的"周六001"同时映射到"001"
    for key, val in list(match_map.items()):
        if key.startswith('周') and len(key) >= 4:
            num_part = key[3:]  # 如 "001"
            if num_part not in match_map:
                match_map[num_part] = val
    
    return match_map


def analyze_feedback_patterns():
    """主分析函数"""
    print(f'\n{"="*60}')
    print(f'竞彩反馈学习引擎 V2')
    print(f'数据获取时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'{"="*60}\n')
    
    # ===== 1. 加载反馈数据 =====
    feedback_raw = rd(FEEDBACK_FILE)
    if not feedback_raw:
        print('❌ feedback.json 不存在或为空')
        return
    feedback = json.loads(feedback_raw)
    dates = feedback.get('dates', {})
    print(f'[1/6] 加载反馈数据: {len(dates)} 个日期')
    
    # ===== 2. 构建 match 映射 =====
    match_map = build_match_map()
    print(f'[2/6] 构建比赛映射: {len(match_map)} 场')
    
    # ===== 3. 加载比分历史 =====
    scores_raw = rd(SCORES_HISTORY)
    scores_obj = json.loads(scores_raw) if scores_raw else {}
    scores_list = scores_obj.get('records', []) if isinstance(scores_obj, dict) else (scores_obj if isinstance(scores_obj, list) else [])
    scores_map = {}
    for s in scores_list:
        if not isinstance(s, dict):
            continue
        mn = s.get('match_num', s.get('matchnum', ''))
        if mn:
            scores_map[mn] = s
    print(f'[3/6] 加载比分历史: {len(scores_map)} 场')
    
    # ===== 4. 分析各维度 =====
    print(f'\n[4/6] 分析各维度准确率...\n')
    
    # 4a. 联赛准确率
    league_stats = {}
    # 4b. 信心度准确率
    conf_stats = {}
    # 4c. 组合模式准确率
    combo_stats = {}
    # 4d. 庄家盈亏方向准确率
    profit_dir_stats = {}
    # 4e. 盘路匹配度准确率（高/中/低）
    panlu_stats = {'高': {'total': 0, 'correct': 0}, '中': {'total': 0, 'correct': 0}, '低': {'total': 0, 'correct': 0}}
    # 4f. 让球预测准确率
    rq_stats = {'total': 0, 'correct': 0}
    # 4g. 竞彩vs让球一致性
    consistency_stats = {'一致': 0, '不一致': 0, '一致且正确': 0}
    
    # 4h. 专家盘路模式收集
    expert_patterns_collected = []
    if HAS_EXPERT_ENGINE:
        expert_engine = ExpertPatternEngine()
        print(f'[专家引擎] 已加载 {len(expert_engine.patterns)} 条内置模式')
    
    # 记录已处理场次（避免重复）
    processed = set()
    
    for date, date_data in dates.items():
        for fb in date_data.get('feedback', []):
            match_num = fb.get('match_num', '')
            # 补全星期几前缀
            if match_num and not match_num.startswith('周'):
                # 从日期推断
                try:
                    from datetime import datetime as dt
                    dt_obj = dt.strptime(date, '%Y-%m-%d')
                    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                    match_num = weekday_names[dt_obj.weekday()] + match_num[2:]
                except:

                    log.warn(f"[learn] 解析异常")
            # 标准化 match_num：补齐编号为3位（"周五1"→"周五001"）
            if match_num and len(match_num) >= 3 and match_num[0] == '周':
                prefix = match_num[:3]  # "周五" + 一位数字 or "周日" 等
                num_part = match_num[3:]
                if num_part.isdigit() and len(num_part) < 3:
                    match_num = prefix + num_part.zfill(3)
                # 如果前缀只有2位（如"周一1"）
                elif len(match_num) >= 2 and match_num[:2] in ['周一','周二','周三','周四','周五','周六','周日']:
                    weekday = match_num[:2]
                    num_part = match_num[2:]
                    if num_part.isdigit() and len(num_part) < 3:
                        match_num = weekday + num_part.zfill(3)
            
            key = f'{date}_{match_num}'
            if key in processed:
                continue
            processed.add(key)
            
            # 优先从 meta.json 获取联赛名（修复联赛:未知问题）
            # match_map 的 key 是 matchnum（如"周四001"），不是 date_matchnum
            meta_league = ''
            if match_num in match_map:
                meta_league = match_map[match_num].get('meta', {}).get('league', '')
            # 也尝试用编号部分（如"001"）查找
            if not meta_league and len(match_num) >= 4 and match_num[:2].startswith('周'):
                num_only = match_num[3:]  # "001"
                if num_only in match_map:
                    meta_league = match_map[num_only].get('meta', {}).get('league', '')
            league = fb.get('league', '') or meta_league or '未知'
            confidence = fb.get('confidence', '-')
            predicted = fb.get('predicted', '')
            actual = fb.get('actual', '')
            is_correct = fb.get('correct', False)
            rq_correct = fb.get('rq_correct', False)
            rq_pred = fb.get('rq_pred', '')
            score = fb.get('score', '')
            
            # 联赛统计
            if league not in league_stats:
                league_stats[league] = {'total': 0, 'correct': 0}
            league_stats[league]['total'] += 1
            if is_correct:
                league_stats[league]['correct'] += 1
            
            # 信心度统计
            if confidence not in conf_stats:
                conf_stats[confidence] = {'total': 0, 'correct': 0}
            conf_stats[confidence]['total'] += 1
            if is_correct:
                conf_stats[confidence]['correct'] += 1
            
            # 让球统计
            rq_stats['total'] += 1
            if rq_correct:
                rq_stats['correct'] += 1
            
            # 一致性统计
            pred_main = predicted
            pred_rq = rq_pred
            if pred_main and pred_rq:
                if pred_main == pred_rq:
                    consistency_stats['一致'] += 1
                    if is_correct:
                        consistency_stats['一致且正确'] += 1
                else:
                    consistency_stats['不一致'] += 1
            
            # 查找对应的比赛数据
            match_info = match_map.get(match_num, {})
            report_content = ''
            if match_info.get('report') and os.path.exists(match_info['report']):
                report_content = rd(match_info['report'])
            
            # 提取组合特征
            combo = {}
            if report_content:
                combo = extract_combo_from_report(report_content)
            
            # 提取 step25/26 数据
            match_dir = match_info.get('dir', '')
            match_date = match_info.get('date', '')
            s25_data = {}
            s26_data = {}
            if match_dir:
                s25_data = extract_step25_data(match_dir, match_date)
                s26_data = extract_step26_data(match_dir, match_date)
            
            # 组合模式分析 - 多维度组合
            combo_tags = []
            
            # ===== 专家盘路模式匹配 =====
            if HAS_EXPERT_ENGINE:
                # 提取欧赔数值
                home_odds = combo.get('欧赔即胜', combo.get('欧赔初胜'))
                away_odds = combo.get('欧赔即负', combo.get('欧赔初负'))
                draw_odds = combo.get('欧赔即平', combo.get('欧赔初平'))
                
                # 提取亚盘信息
                asian_line = combo.get('澳门亚盘', '')
                asian_change = ''
                # 从竞彩欧赔盘路推断变化方向
                jingcai_change = combo.get('竞彩欧赔盘路', combo.get('竞彩欧赔盘路_基准', ''))
                
                factor, pattern = expert_engine.match(
                    league=league,
                    home_odds=home_odds,
                    away_odds=away_odds,
                    draw_odds=draw_odds,
                    odds_change=jingcai_change,
                    asian_line=asian_line,
                    asian_change=asian_change,
                )
                
                if factor is not None and pattern is not None:
                    expert_patterns_collected.append({
                        'match_num': match_num,
                        'date': date,
                        'league': league,
                        'predicted': predicted,
                        'actual': actual,
                        'correct': is_correct,
                        'factor': factor,
                        'pattern': pattern,
                    })
            
            # 1. 单维度标签
            # 欧赔方向
            if '欧赔趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}')
            
            # 让球方向
            if '让球趋势_dir' in combo:
                combo_tags.append(f'让球:{combo["让球趋势_dir"]}')
            
            # 亚盘方向
            if '亚盘趋势_dir' in combo:
                combo_tags.append(f'亚盘:{combo["亚盘趋势_dir"]}')
            
            # 百家方向
            if '百家对比_dir' in combo:
                combo_tags.append(f'百家:{combo["百家对比_dir"]}')
            
            # 盘路匹配
            if '盘路匹配' in combo:
                combo_tags.append(f'盘路:{combo["盘路匹配"]}')
                panlu_key = combo['盘路匹配']
                if panlu_key in panlu_stats:
                    panlu_stats[panlu_key]['total'] += 1
                    if is_correct:
                        panlu_stats[panlu_key]['correct'] += 1
            
            # 庄家方向
            if s25_data.get('庄家方向'):
                combo_tags.append(f'庄家:{s25_data["庄家方向"]}')
            
            # 大热方
            if s25_data.get('大热方'):
                combo_tags.append(f'大热:{s25_data["大热方"]}')
            
            # ===== 新增：盈亏方向 =====
            if s25_data.get('盈亏方向'):
                combo_tags.append(f'盈亏方向:{s25_data["盈亏方向"]}')
            
            # ===== 新增：投注占比 =====
            if s26_data.get('投注占比_主'):
                bet_main = s26_data['投注占比_主']
                try:
                    bet_val = float(str(bet_main).replace('%', ''))
                    if bet_val >= 45:
                        combo_tags.append('投注占比:高(≥45%)')
                    elif bet_val >= 30:
                        combo_tags.append('投注占比:中(30-44%)')
                    else:
                        combo_tags.append('投注占比:低(<30%)')
                except:
                    combo_tags.append(f'投注占比:{bet_main}')
            
            # ===== 新增：盈亏占比 =====
            if s26_data.get('盈亏占比_主'):
                profit_main = s26_data['盈亏占比_主']
                try:
                    profit_val = float(str(profit_main))
                    if profit_val >= 0.4:
                        combo_tags.append('盈亏占比:高(≥0.4)')
                    elif profit_val >= 0.2:
                        combo_tags.append('盈亏占比:中(0.2-0.39)')
                    else:
                        combo_tags.append('盈亏占比:低(<0.2)')
                except:
                    combo_tags.append(f'盈亏占比:{profit_main}')
            
            # 信心度区间
            if combo.get('confidence'):
                conf_val = combo['confidence']
                if conf_val >= 70:
                    combo_tags.append('信心:高(≥70%)')
                elif conf_val >= 55:
                    combo_tags.append('信心:中(55-69%)')
                else:
                    combo_tags.append('信心:低(<55%)')
            
            # 联赛标签
            combo_tags.append(f'联赛:{league}')
            
            # ===== 精细化组合标签（细粒度模式）=====
            # 这些标签用于学习更精确的模式，如：
            # "澳门让半球 × 竞彩盘路升升降 × 投注占比(胜20%/平30%/负50%) → 胜场90%"
            
            # --- 1. 澳门亚盘具体盘口 ---
            asian_handicap = combo.get('澳门亚盘', '')
            if asian_handicap and asian_handicap != '未知':
                combo_tags.append(f'澳门亚盘:{asian_handicap}')
            
            # --- 2. 欧赔竞彩盘路 ---
            jingcai_panlu = combo.get('竞彩欧赔盘路', combo.get('竞彩欧赔盘路_基准', ''))
            if jingcai_panlu:
                combo_tags.append(f'竞彩盘路:{jingcai_panlu}')
            
            # --- 3. 欧赔IW盘路 ---
            iw_panlu = combo.get('IW欧赔盘路', combo.get('IW欧赔盘路_基准', ''))
            if iw_panlu:
                combo_tags.append(f'IW盘路:{iw_panlu}')
            
            # --- 4. 百家欧赔盘路 ---
            baijia_panlu = combo.get('百家欧赔盘路', combo.get('百家欧赔盘路_基准', ''))
            if baijia_panlu:
                combo_tags.append(f'百家盘路:{baijia_panlu}')
            
            # --- 5. 澳门亚盘同赔分布 ---
            macau_dist = combo.get('澳门亚盘同赔分布', {})
            if macau_dist:
                # 找出占比最高的盘路类型
                top_type = max(macau_dist, key=macau_dist.get)
                combo_tags.append(f'澳门同赔:{top_type}')
            
            # --- 6. 投注占比精确分布 ---
            bet_main = s26_data.get('投注占比_主', '')
            bet_ping = s26_data.get('投注占比_平', '')
            bet_ke = s26_data.get('投注占比_客', '')
            if bet_main and bet_ping and bet_ke:
                try:
                    bm = float(str(bet_main).replace('%', ''))
                    bp = float(str(bet_ping).replace('%', ''))
                    bk = float(str(bet_ke).replace('%', ''))
                    # 生成精确分布标签（四舍五入到10%）
                    bm_r = round(bm / 10) * 10
                    bp_r = round(bp / 10) * 10
                    bk_r = round(bk / 10) * 10
                    combo_tags.append(f'投注占比精确:胜{bm_r}%平{bp_r}%负{bk_r}%')
                except:

                    log.warn(f"[learn] 解析异常")
            # --- 7. 庄家盈亏精确模式 ---
            # 从step26提取胜/平/负各自盈亏（赢钱/亏钱）
            s26_zw = s26_data.get('庄家胜盈亏', '')
            s26_zp = s26_data.get('庄家平盈亏', '')
            s26_zk = s26_data.get('庄家负盈亏', '')
            if s26_zw and s26_zp and s26_zk:
                win_label = '赢' if '赢' in s26_zw else ('亏' if '亏' in s26_zw else s26_zw[:1])
                ping_label = '赢' if '赢' in s26_zp else ('亏' if '亏' in s26_zp else s26_zp[:1])
                ke_label = '赢' if '赢' in s26_zk else ('亏' if '亏' in s26_zk else s26_zk[:1])
                combo_tags.append(f'庄家盈亏:胜{win_label}平{ping_label}负{ke_label}')
            
            # 庄家最看好
            zhu_kan_hao = s26_data.get('庄家最看好', '')
            if zhu_kan_hao:
                combo_tags.append(f'庄家看好:{zhu_kan_hao}')
            
            # ===== 精细化二维组合 =====
            # 澳门亚盘 × 欧赔盘路
            if asian_handicap and asian_handicap != '未知' and jingcai_panlu:
                combo_tags.append(f'澳门亚盘:{asian_handicap}×竞彩盘路:{jingcai_panlu}')
            if asian_handicap and asian_handicap != '未知' and iw_panlu:
                combo_tags.append(f'澳门亚盘:{asian_handicap}×IW盘路:{iw_panlu}')
            
            # 欧赔盘路 × 投注占比
            if jingcai_panlu:
                if combo_tags[-1].startswith('投注占比精确:'):
                    combo_tags.append(f'竞彩盘路:{jingcai_panlu}×{combo_tags[-1]}')
            
            # 庄家盈亏 × 投注占比
            if combo_tags[-1].startswith('庄家盈亏:'):
                # 找上一个投注占比标签
                for tag in reversed(combo_tags):
                    if tag.startswith('投注占比精确:'):
                        combo_tags.append(f'{combo_tags[-1]}×{tag}')
                        break
            
            # 澳门亚盘 × 庄家盈亏
            if asian_handicap and asian_handicap != '未知':
                for tag in reversed(combo_tags):
                    if tag.startswith('庄家盈亏:'):
                        combo_tags.append(f'澳门亚盘:{asian_handicap}×{tag}')
                        break
            
            # ===== 精细化三维组合 =====
            # 澳门亚盘 × 竞彩盘路 × 庄家盈亏
            if asian_handicap and asian_handicap != '未知' and jingcai_panlu:
                for tag in reversed(combo_tags):
                    if tag.startswith('庄家盈亏:'):
                        combo_tags.append(f'澳门亚盘:{asian_handicap}×竞彩盘路:{jingcai_panlu}×{tag}')
                        break
            
            # 澳门亚盘 × IW盘路 × 庄家盈亏
            if asian_handicap and asian_handicap != '未知' and iw_panlu:
                for tag in reversed(combo_tags):
                    if tag.startswith('庄家盈亏:'):
                        combo_tags.append(f'澳门亚盘:{asian_handicap}×IW盘路:{iw_panlu}×{tag}')
                        break
            
            # 竞彩盘路 × IW盘路 × 联赛
            if jingcai_panlu and iw_panlu:
                combo_tags.append(f'竞彩盘路:{jingcai_panlu}×IW盘路:{iw_panlu}×联赛:{league}')
            
            # 澳门亚盘 × 竞彩盘路 × IW盘路
            if asian_handicap and asian_handicap != '未知' and jingcai_panlu and iw_panlu:
                combo_tags.append(f'澳门亚盘:{asian_handicap}×竞彩盘路:{jingcai_panlu}×IW盘路:{iw_panlu}')
            
            # 澳门亚盘 × 竞彩盘路 × IW盘路 × 联赛
            if asian_handicap and asian_handicap != '未知' and jingcai_panlu and iw_panlu:
                combo_tags.append(f'澳门亚盘:{asian_handicap}×竞彩盘路:{jingcai_panlu}×IW盘路:{iw_panlu}×联赛:{league}')
            
            # ===== 收集各维度的值（统一变量名）=====
            dim_values = {}
            dim_labels = {
                '欧赔': combo.get('欧赔趋势_dir'),
                '让球': combo.get('让球趋势_dir'),
                '亚盘': combo.get('亚盘趋势_dir'),
                '百家': combo.get('百家对比_dir'),
                '盘路': combo.get('盘路匹配'),
                '庄家': s25_data.get('庄家方向'),
                '大热': s25_data.get('大热方'),
                '盈亏方向': s25_data.get('盈亏方向'),
                '信心': None,
            }
            # 信心度需要转换
            if combo.get('confidence'):
                conf_val = combo['confidence']
                if conf_val >= 70:
                    dim_labels['信心'] = '高'
                elif conf_val >= 55:
                    dim_labels['信心'] = '中'
                else:
                    dim_labels['信心'] = '低'
            # 投注占比需要转换
            if s26_data.get('投注占比_主'):
                try:
                    bet_val = float(str(s26_data['投注占比_主']).replace('%', ''))
                    dim_labels['投注占比'] = '高' if bet_val >= 45 else ('中' if bet_val >= 30 else '低')
                except:
                    dim_labels['投注占比'] = '中'
            else:
                dim_labels['投注占比'] = None
            # 盈亏占比需要转换
            if s26_data.get('盈亏占比_主'):
                try:
                    profit_val = float(str(s26_data['盈亏占比_主']))
                    dim_labels['盈亏占比'] = '高' if profit_val >= 0.4 else ('中' if profit_val >= 0.2 else '低')
                except:
                    dim_labels['盈亏占比'] = '中'
            else:
                dim_labels['盈亏占比'] = None
            
            # ===== 2. 双维度组合标签 =====
            # 所有维度 × 联赛
            for dim_name, dim_val in dim_labels.items():
                if dim_val:
                    combo_tags.append(f'{dim_name}:{dim_val}×联赛:{league}')
            
            # ===== 新增：所有维度 × 澳门亚盘 =====
            asian_val = combo.get('亚盘趋势_dir')
            if asian_val:
                for dim_name, dim_val in dim_labels.items():
                    if dim_name != '亚盘' and dim_val:
                        combo_tags.append(f'{dim_name}:{dim_val}×澳门亚盘:{asian_val}')
            
            # ===== 3. 三维度组合标签 =====
            # 原有三维组合
            if '欧赔趋势_dir' in combo and '让球趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×联赛:{league}')
            if '欧赔趋势_dir' in combo and '亚盘趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×联赛:{league}')
            if s25_data.get('庄家方向') and '盘路匹配' in combo:
                combo_tags.append(f'庄家:{s25_data["庄家方向"]}×盘路:{combo["盘路匹配"]}×联赛:{league}')
            
            # 新增：盈亏方向/投注占比/盈亏占比 × 任意二维 × 联赛
            if dim_labels['盈亏方向']:
                if '欧赔趋势_dir' in combo:
                    combo_tags.append(f'盈亏方向:{dim_labels["盈亏方向"]}×欧赔:{combo["欧赔趋势_dir"]}×联赛:{league}')
                if '让球趋势_dir' in combo:
                    combo_tags.append(f'盈亏方向:{dim_labels["盈亏方向"]}×让球:{combo["让球趋势_dir"]}×联赛:{league}')
                if '亚盘趋势_dir' in combo:
                    combo_tags.append(f'盈亏方向:{dim_labels["盈亏方向"]}×亚盘:{combo["亚盘趋势_dir"]}×联赛:{league}')
                if '盘路匹配' in combo:
                    combo_tags.append(f'盈亏方向:{dim_labels["盈亏方向"]}×盘路:{combo["盘路匹配"]}×联赛:{league}')
            
            if dim_labels['投注占比']:
                if '欧赔趋势_dir' in combo:
                    combo_tags.append(f'投注占比:{dim_labels["投注占比"]}×欧赔:{combo["欧赔趋势_dir"]}×联赛:{league}')
                if '让球趋势_dir' in combo:
                    combo_tags.append(f'投注占比:{dim_labels["投注占比"]}×让球:{combo["让球趋势_dir"]}×联赛:{league}')
                if '亚盘趋势_dir' in combo:
                    combo_tags.append(f'投注占比:{dim_labels["投注占比"]}×亚盘:{combo["亚盘趋势_dir"]}×联赛:{league}')
                if '盘路匹配' in combo:
                    combo_tags.append(f'投注占比:{dim_labels["投注占比"]}×盘路:{combo["盘路匹配"]}×联赛:{league}')
            
            if dim_labels['盈亏占比']:
                if '欧赔趋势_dir' in combo:
                    combo_tags.append(f'盈亏占比:{dim_labels["盈亏占比"]}×欧赔:{combo["欧赔趋势_dir"]}×联赛:{league}')
                if '让球趋势_dir' in combo:
                    combo_tags.append(f'盈亏占比:{dim_labels["盈亏占比"]}×让球:{combo["让球趋势_dir"]}×联赛:{league}')
                if '亚盘趋势_dir' in combo:
                    combo_tags.append(f'盈亏占比:{dim_labels["盈亏占比"]}×亚盘:{combo["亚盘趋势_dir"]}×联赛:{league}')
                if '盘路匹配' in combo:
                    combo_tags.append(f'盈亏占比:{dim_labels["盈亏占比"]}×盘路:{combo["盘路匹配"]}×联赛:{league}')
            
            # ===== 新增：三维度 × 澳门亚盘 =====
            if asian_val:
                if '欧赔趋势_dir' in combo:
                    combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if '让球趋势_dir' in combo:
                    combo_tags.append(f'让球:{combo["让球趋势_dir"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if s25_data.get('庄家方向'):
                    combo_tags.append(f'庄家:{s25_data["庄家方向"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if '盘路匹配' in combo:
                    combo_tags.append(f'盘路:{combo["盘路匹配"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if dim_labels['盈亏方向']:
                    combo_tags.append(f'盈亏方向:{dim_labels["盈亏方向"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if dim_labels['投注占比']:
                    combo_tags.append(f'投注占比:{dim_labels["投注占比"]}×澳门亚盘:{asian_val}×联赛:{league}')
                if dim_labels['盈亏占比']:
                    combo_tags.append(f'盈亏占比:{dim_labels["盈亏占比"]}×澳门亚盘:{asian_val}×联赛:{league}')
            
            # ===== 4. 四维度组合标签 =====
            # 原有四维组合
            if '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and '亚盘趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×联赛:{league}')
            if '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and s25_data.get('庄家方向'):
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×庄家:{s25_data["庄家方向"]}×联赛:{league}')
            
            # 新增：盈亏方向/投注占比/盈亏占比 进入四维组合
            if '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and '亚盘趋势_dir' in combo:
                if s25_data.get('庄家方向'):
                    combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×庄家:{s25_data["庄家方向"]}×联赛:{league}')
            if dim_labels['盈亏方向'] and '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and '亚盘趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×盈亏方向:{dim_labels["盈亏方向"]}×联赛:{league}')
            if dim_labels['投注占比'] and '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and '亚盘趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×投注占比:{dim_labels["投注占比"]}×联赛:{league}')
            if dim_labels['盈亏占比'] and '欧赔趋势_dir' in combo and '让球趋势_dir' in combo and '亚盘趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×亚盘:{combo["亚盘趋势_dir"]}×盈亏占比:{dim_labels["盈亏占比"]}×联赛:{league}')
            
            # 新增：四维 × 澳门亚盘
            if asian_val and '欧赔趋势_dir' in combo and '让球趋势_dir' in combo:
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×让球:{combo["让球趋势_dir"]}×澳门亚盘:{asian_val}×联赛:{league}')
            if asian_val and '欧赔趋势_dir' in combo and s25_data.get('庄家方向'):
                combo_tags.append(f'欧赔:{combo["欧赔趋势_dir"]}×庄家:{s25_data["庄家方向"]}×澳门亚盘:{asian_val}×联赛:{league}')
            if asian_val and '让球趋势_dir' in combo and s25_data.get('庄家方向'):
                combo_tags.append(f'让球:{combo["让球趋势_dir"]}×庄家:{s25_data["庄家方向"]}×澳门亚盘:{asian_val}×联赛:{league}')
            
            # 记录每个组合标签的准确率
            for tag in combo_tags:
                if tag not in combo_stats:
                    combo_stats[tag] = {'total': 0, 'correct': 0}
                combo_stats[tag]['total'] += 1
                if is_correct:
                    combo_stats[tag]['correct'] += 1
            
            # 庄家盈亏方向统计
            if s25_data.get('庄家方向'):
                dir_key = s25_data['庄家方向']
                if dir_key not in profit_dir_stats:
                    profit_dir_stats[dir_key] = {'total': 0, 'correct': 0}
                profit_dir_stats[dir_key]['total'] += 1
                if is_correct:
                    profit_dir_stats[dir_key]['correct'] += 1
            
            # 写入 feedback.json 的 combo 字段
            if combo and match_num:
                for date_key, date_val in dates.items():
                    for fb_item in date_val.get('feedback', []):
                        fb_mn = fb_item.get('match_num', '')
                        if fb_mn == match_num or fb_mn == match_num[2:]:
                            fb_item['combos'] = combo
                            fb_item['s25'] = s25_data
                            fb_item['s26'] = s26_data
                            break
    
    print(f'   已分析: {len(processed)} 场')
    
    # ===== 5. 生成学习结果 =====
    print(f'\n[5/6] 生成学习结果...\n')
    
    # 5a. 高准确率组合（≥60%且≥5场）
    # 修复：低准确率组合提高阈值到≥10场，避免n=5的偶然低准确率被惩罚
    high_combos = []
    low_combos = []
    for tag, stats in combo_stats.items():
        acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        # 高准确率：≥5场且≥60%
        if stats['total'] >= 5 and acc >= 0.60:
            high_combos.append({
                'tag': tag,
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
            })
        # 低准确率：≥10场且≤35%（提高样本阈值，避免偶然低准确率被惩罚）
        elif stats['total'] >= 10 and acc <= 0.35:
            low_combos.append({
                'tag': tag,
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
            })
    
    high_combos.sort(key=lambda x: x['accuracy'], reverse=True)
    low_combos.sort(key=lambda x: x['accuracy'])
    
    # 5b. 联赛准确率排序（提高最小样本到≥5场）
    league_ranked = []
    for league, stats in league_stats.items():
        if stats['total'] >= 5:
            acc = stats['correct'] / stats['total']
            league_ranked.append({
                'league': league,
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
            })
    league_ranked.sort(key=lambda x: x['accuracy'], reverse=True)
    
    # 5c. 信心度修正表（提高最小样本到≥5场）
    conf_adjust = {}
    for conf, stats in conf_stats.items():
        if stats['total'] >= 5:
            acc = stats['correct'] / stats['total']
            # 计算修正系数：实际准确率 / 标称准确率
            m = re.search(r'(\d+)%', conf)
            nominal = int(m.group(1)) / 100.0 if m else 0.5
            adjust_factor = round(acc / nominal, 2) if nominal > 0 else 1.0
            conf_adjust[conf] = {
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
                'nominal': round(nominal, 2),
                'adjust_factor': adjust_factor,
            }
    
    # 5d. 庄家盈亏方向统计（提高最小样本到≥5场）
    profit_ranked = []
    for dir_key, stats in profit_dir_stats.items():
        if stats['total'] >= 5:
            acc = stats['correct'] / stats['total']
            profit_ranked.append({
                'direction': dir_key,
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
            })
    profit_ranked.sort(key=lambda x: x['accuracy'], reverse=True)
    
    # 5e. 盘路匹配度统计（提高最小样本到≥5场）
    panlu_ranked = []
    for level, stats in panlu_stats.items():
        if stats['total'] >= 5:
            acc = stats['correct'] / stats['total']
            panlu_ranked.append({
                'level': level,
                'accuracy': round(acc, 3),
                'total': stats['total'],
                'correct': stats['correct'],
            })
    panlu_ranked.sort(key=lambda x: x['accuracy'], reverse=True)
    
    # ===== 6. 保存 =====
    print(f'[6/6] 保存学习结果...\n')
    
    learned = {
        'version': '2.0',
        'updated': datetime.now().isoformat(),
        'total_matches': len(processed),
        'total_dates': len(dates),
        
        # 核心学习结果
        'high_accuracy_combos': high_combos,
        'low_accuracy_combos': low_combos,
        'expert_patterns': expert_patterns_collected,
        
        # 维度统计
        'league_accuracy': league_ranked,
        'confidence_accuracy': conf_adjust,
        'profit_direction_accuracy': profit_ranked,
        'panlu_accuracy': panlu_ranked,
        
        # 其他统计
        'handicap_accuracy': {
            'total': rq_stats['total'],
            'correct': rq_stats['correct'],
            'accuracy': round(rq_stats['correct'] / rq_stats['total'], 3) if rq_stats['total'] > 0 else 0,
        },
        'prediction_consistency': consistency_stats,
        
        # 原始数据（供调试）
        '_raw_league_stats': league_stats,
        '_raw_conf_stats': conf_stats,
        '_raw_combo_stats': {k: v for k, v in combo_stats.items() if v['total'] >= 3},
    }
    
    with open(LEARNED_FILE, 'w', encoding='utf-8') as f:
        json.dump(learned, f, ensure_ascii=False, indent=2)
    
    # 同时更新 feedback.json（写入 combo 数据）
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)
    
    # ===== 输出摘要 =====
    print(f'\n{"="*60}')
    print(f'学习结果摘要')
    print(f'{"="*60}')
    
    print(f'\n总场次: {len(processed)} 场, {len(dates)} 个日期')
    
    print(f'\n高准确率组合 (>=60%, >=5场):')
    for c in high_combos[:15]:
        print(f'   {c["tag"]}: {c["accuracy"]*100:.0f}% ({c["correct"]}/{c["total"]})')
    
    print(f'\n低准确率组合 (<=35%, >=5场):')
    for c in low_combos[:10]:
        print(f'   {c["tag"]}: {c["accuracy"]*100:.0f}% ({c["correct"]}/{c["total"]})')
    
    print(f'\n联赛准确率 TOP10:')
    for l in league_ranked[:10]:
        print(f'   {l["league"]}: {l["accuracy"]*100:.0f}% ({l["correct"]}/{l["total"]})')
    
    print(f'\n信心度修正:')
    for conf, adj in sorted(conf_adjust.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
        print(f'   {conf}: 实际{adj["accuracy"]*100:.0f}% (标称{adj["nominal"]*100:.0f}%, 修正系数{adj["adjust_factor"]:.2f})')
    
    print(f'\n庄家盈亏方向:')
    for p in profit_ranked[:5]:
        print(f'   {p["direction"]}: {p["accuracy"]*100:.0f}% ({p["correct"]}/{p["total"]})')
    
    print(f'\n盘路匹配度:')
    for p in panlu_ranked:
        print(f'   {p["level"]}: {p["accuracy"]*100:.0f}% ({p["correct"]}/{p["total"]})')
    
    print(f'\n✅ 学习结果已保存: {LEARNED_FILE}')
    print(f'✅ feedback.json 已更新（写入 combo/s25/s26 数据）')
    
    return learned


if __name__ == '__main__':
    analyze_feedback_patterns()
