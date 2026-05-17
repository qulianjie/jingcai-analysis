# -*- coding: utf-8 -*-
"""
竞彩专家盘路模式引擎 V4 - 精确到小数点后一位

基于连杰实战经验，将盘路变化+赔率数值+联赛三维组合进行精确匹配

用法：
    from expert_pattern_engine import ExpertPatternEngine
    engine = ExpertPatternEngine()
    factor = engine.match(league='法甲', home_odds=1.85, asian_line='半球', asian_change='降')
    # → 返回 (0.0, {'league': '法甲', 'pattern': '半球降半球平', 'outcome': '平', 'sample': 5})
"""
import os
import math


class ExpertPatternEngine:
    """专家盘路模式引擎"""
    
    def __init__(self, patterns_file=None):
        """初始化，加载内置模式库"""
        self.patterns = self._build_patterns()
        if patterns_file and os.path.exists(patterns_file):
            self._load_custom(patterns_file)
    
    def _build_patterns(self):
        """构建内置模式库（基于连杰实战经验）
        
        每条模式格式：
        {
            'league': '联赛关键词',        # 如'法甲'、'德甲'、''(任意联赛)
            'odds_range': {'home':(1.8,1.9), 'away':(2.2,2.3), 'draw':None},  # 赔率范围（小数点后一位）
            'odds_change': '升降降',        # 竞彩欧赔盘路变化
            'asian_line': '半球',           # 亚盘盘口
            'asian_change': '降',           # 亚盘变化方向：升/降/不变
            'outcome': '平',                # 结果倾向：胜/负/平/不胜
            'sample': 5,                    # 样本量
            'note': '都是平',               # 备注
        }
        """
        return [
            # ===== 亚盘盘口变化模式 =====
            
            # 法甲
            {'league': '法甲', 'odds_range': None, 'odds_change': None,
             'asian_line': '半球', 'asian_change': '降', 'asian_to': '半球平',
             'outcome': '平', 'sample': 5, 'note': '都是平'},
            {'league': '法甲', 'odds_range': None, 'odds_change': None,
             'asian_line': '受半', 'asian_change': '降', 'asian_to': '受半球平',
             'outcome': '负', 'sample': 4, 'note': '受让方输'},
            
            # 意甲
            {'league': '意甲', 'odds_range': None, 'odds_change': None,
             'asian_line': '平半', 'asian_change': '升', 'asian_to': '半',
             'outcome': '不胜', 'sample': 5, 'note': '主胜和客胜都难'},
            {'league': '意甲', 'odds_range': {'away': (2.2, 2.3)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '胜', 'sample': 4, 'note': '客2.2几 客队赢'},
            {'league': '意甲', 'odds_range': {'home': (2.2, 2.3)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '负', 'sample': 4, 'note': '主2.2几 主队输'},
            {'league': '意甲', 'odds_range': {'home': (2.3, 2.4)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '胜', 'sample': 4, 'note': '主2.3几 主队赢'},
            
            # 西甲
            {'league': '西甲', 'odds_range': None, 'odds_change': None,
             'asian_line': '半一', 'asian_change': '降', 'asian_to': '半',
             'outcome': '负', 'sample': 5, 'note': '让球方输'},
            
            # 德甲
            {'league': '德甲', 'odds_range': {'home': (1.8, 1.9)}, 'odds_change': '升降升',
             'asian_line': None, 'asian_change': None,
             'outcome': '赢', 'sample': 5, 'note': '1.8几升降升 几乎全赢'},
            {'league': '德甲', 'odds_range': {'home': (1.7, 1.8)}, 'odds_change': '升降降',
             'asian_line': '一球', 'asian_change': '降', 'asian_to': '半一',
             'outcome': '负', 'sample': 3, 'note': '1.7几主 升降降 一球0.75降到0.5 负'},
            {'league': '德甲', 'odds_range': {'home': (1.1, 1.2), 'draw': (1.2, 1.3)}, 'odds_change': '升降降',
             'asian_line': '一球', 'asian_change': '降', 'asian_to': '半一',
             'outcome': '平', 'sample': 3, 'note': '1.8/1.7主 升降降 一球0.75降到0.5 1.1几平1.2几升'},
            {'league': '德甲', 'odds_range': {'away': (2.2, 2.3)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '胜', 'sample': 5, 'note': '客2.2几 客队全赢'},
            {'league': '德甲', 'odds_range': None, 'odds_change': None,
             'asian_line': '平', 'asian_change': '升', 'asian_to': '平半',
             'outcome': '平', 'sample': 5, 'note': '平升平半 都是平'},
            
            # 英超
            {'league': '英超', 'odds_range': None, 'odds_change': None,
             'asian_line': '半', 'asian_change': '升', 'asian_to': '半一',
             'outcome': '胜', 'sample': 5, 'note': '半升半一 让球方赢'},
            {'league': '英超', 'odds_range': {'away': (2.1, 2.2)}, 'odds_change': '升降降',
             'asian_line': None, 'asian_change': None,
             'outcome': '客负', 'sample': 4, 'note': '客2.1升降降 客队输'},
            {'league': '英超', 'odds_range': {'away': (5.0, 5.9)}, 'odds_change': '降升升',
             'asian_line': '让0.75', 'asian_change': '降',
             'outcome': '负', 'sample': 5, 'note': '让0.75降升升 5.几都是负'},
            
            # 韩职
            {'league': '韩职', 'odds_range': {'home': (2.1, 2.2)}, 'odds_change': '升降降',
             'asian_line': None, 'asian_change': None,
             'outcome': '胜', 'sample': 4, 'note': '2.1升降降 胜'},
            
            # 日乙
            {'league': '日乙', 'odds_range': {'home': (2.2, 2.3)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '不胜', 'sample': 5, 'note': '2.2不胜'},
            
            # 荷兰
            {'league': '荷兰', 'odds_range': None, 'odds_change': None,
             'asian_line': '平半', 'asian_change': '升', 'asian_to': '半',
             'outcome': '负', 'sample': 4, 'note': '平半升半 让球方输（与葡萄牙相反）'},
            {'league': '荷兰', 'odds_range': None, 'odds_change': None,
             'asian_line': '平', 'asian_change': '升', 'asian_to': '平半',
             'outcome': '负', 'sample': 3, 'note': '平升平半 负'},
            
            # 葡萄牙
            {'league': '葡萄牙', 'odds_range': None, 'odds_change': None,
             'asian_line': '平半', 'asian_change': '升', 'asian_to': '半',
             'outcome': '胜', 'sample': 4, 'note': '平半升半 胜（与荷兰相反！）'},
            
            # 中国
            {'league': '中国', 'odds_range': None, 'odds_change': '不变降升',
             'asian_line': None, 'asian_change': None,
             'outcome': '负', 'sample': 4, 'note': '不变降升 负'},
            {'league': '中国', 'odds_range': None, 'odds_change': '升降降',
             'asian_line': None, 'asian_change': None,
             'outcome': '平', 'sample': 4, 'note': '升降降 平'},
            
            # 通用模式（跨联赛）
            {'league': '', 'odds_range': None, 'odds_change': '升降升',
             'asian_line': None, 'asian_change': None,
             'outcome': '平', 'sample': 5, 'note': '升降升+前一天分胜负→第二天几乎平',
             'condition': '前一天分胜负'},
            {'league': '', 'odds_range': None, 'odds_change': '升降升',
             'asian_line': None, 'asian_change': None,
             'outcome': '客胜', 'sample': 4, 'note': '升降升+客低→客胜',
             'condition': '客队赔率低'},
            
            # ===== 精确赔率组合模式 =====
            {'league': '', 'odds_range': {'home': (2.2, 2.3), 'draw': (2.3, 2.4)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '胜', 'sample': 3, 'note': '2.25/2.4 胜'},
            {'league': '', 'odds_range': {'home': (2.3, 2.4), 'draw': (2.4, 2.5)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '平', 'sample': 3, 'note': '2.35/2.45 平'},
            {'league': '', 'odds_range': {'home': (2.2, 2.3)}, 'odds_change': None,
             'asian_line': None, 'asian_change': None,
             'outcome': '负', 'sample': 3, 'note': '2.2 负'},
        ]
    
    def _load_custom(self, patterns_file):
        """加载用户自定义模式（expert_patterns.md）"""
        try:
            with open(patterns_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 简单解析：从markdown表格提取
            # TODO: 后续可以做得更智能
        except:
            pass
    
    def _odds_in_range(self, odds_val, odds_range):
        """检查赔率是否在范围内（精确到小数点后一位）
        
        例：odds_val=2.25, range=(2.2, 2.3) → True (2.25→2.2，在2.2~2.3之间)
        """
        if odds_val is None or odds_range is None:
            return True
        
        low, high = odds_range
        # 截断到小数点后一位（不是四舍五入）
        truncated = math.floor(odds_val * 10) / 10
        
        return low <= truncated < high
    
    def _match_odds(self, odds_range, home_odds, away_odds, draw_odds):
        """匹配赔率范围
        
        Args:
            odds_range: {'home':(2.2,2.3), 'away':(2.1,2.2), 'draw':None}
            home_odds: 主胜赔率
            away_odds: 客胜赔率
            draw_odds: 平局赔率
        
        Returns:
            (匹配度, 匹配详情)
            匹配度：0.0~1.0，1.0表示完全匹配
        """
        if odds_range is None:
            return 1.0, {}
        
        score = 0
        total_checks = 0
        details = {}
        
        if 'home' in odds_range and odds_range['home']:
            total_checks += 1
            if self._odds_in_range(home_odds, odds_range['home']):
                score += 1
                details['home_match'] = True
            else:
                details['home_match'] = False
        
        if 'away' in odds_range and odds_range['away']:
            total_checks += 1
            if self._odds_in_range(away_odds, odds_range['away']):
                score += 1
                details['away_match'] = True
            else:
                details['away_match'] = False
        
        if 'draw' in odds_range and odds_range['draw']:
            total_checks += 1
            if self._odds_in_range(draw_odds, odds_range['draw']):
                score += 1
                details['draw_match'] = True
            else:
                details['draw_match'] = False
        
        if total_checks == 0:
            return 1.0, details
        
        return score / total_checks, details
    
    def _match_league(self, pattern_league, match_league):
        """匹配联赛"""
        if not pattern_league:
            return True  # 空表示任意联赛
        if not match_league:
            return False
        return pattern_league in match_league or match_league in pattern_league
    
    def _match_asian(self, pattern, asian_line, asian_change):
        """匹配亚盘"""
        if pattern.get('asian_line') and pattern['asian_line'] != asian_line:
            # 模糊匹配：'半球' 匹配 '半球'，'受半' 匹配 '受让半球'
            if pattern['asian_line'] not in asian_line and asian_line not in pattern['asian_line']:
                return False
        
        if pattern.get('asian_change') and pattern['asian_change'] != asian_change:
            return False
        
        return True
    
    def _match_odds_change(self, pattern_odds_change, match_odds_change):
        """匹配欧赔盘路变化"""
        if not pattern_odds_change:
            return True
        if not match_odds_change:
            return False
        return pattern_odds_change in match_odds_change or match_odds_change in pattern_odds_change
    
    def match(self, league='', home_odds=None, away_odds=None, draw_odds=None,
              odds_change='', asian_line='', asian_change='', asian_to='',
              condition=''):
        """
        主入口：匹配专家模式
        
        Args:
            league: 联赛名称（如'法甲'、'德甲'）
            home_odds: 主胜赔率（如1.85）
            away_odds: 客胜赔率（如2.20）
            draw_odds: 平局赔率（如3.10）
            odds_change: 竞彩欧赔盘路变化（如'升降升'、'升降降'）
            asian_line: 亚盘盘口（如'半球'、'平半'）
            asian_change: 亚盘变化（如'升'、'降'、'不变'）
            asian_to: 亚盘变化目标（如'半'、'半球平'）
            condition: 附加条件（如'前一天分胜负'）
        
        Returns:
            (factor, matched_pattern)
            factor: 权重修正系数（0.0~1.5）
            matched_pattern: 匹配到的模式详情
        """
        best_match = None
        best_score = 0
        
        for p in self.patterns:
            score = 0.0
            max_score = 0.0
            
            # 1. 联赛匹配（必须）
            max_score += 3
            if self._match_league(p['league'], league):
                score += 3
            else:
                continue  # 联赛不匹配，跳过
            
            # 2. 赔率范围匹配（精确到小数点后一位）
            if p['odds_range']:
                max_score += 3
                odds_score, odds_details = self._match_odds(
                    p['odds_range'], home_odds, away_odds, draw_odds)
                score += odds_score * 3
            else:
                # 没有赔率限制，给基础分
                score += 1.5
                max_score += 1.5
            
            # 3. 欧赔盘路变化匹配
            if p['odds_change']:
                max_score += 2
                if self._match_odds_change(p['odds_change'], odds_change):
                    score += 2
            else:
                score += 1.0
                max_score += 1.0
            
            # 4. 亚盘匹配
            if p['asian_line'] or p['asian_change']:
                max_score += 2
                asian_ok = True
                if p['asian_line'] and p['asian_line'] not in asian_line:
                    asian_ok = False
                if p['asian_change'] and p['asian_change'] != asian_change:
                    asian_ok = False
                if asian_to and p.get('asian_to') and p['asian_to'] != asian_to:
                    asian_ok = False
                if asian_ok:
                    score += 2
            else:
                score += 1.0
                max_score += 1.0
            
            # 5. 附加条件匹配
            if p.get('condition'):
                max_score += 1
                if condition and p['condition'] in condition:
                    score += 1
            
            # 计算匹配度
            if max_score > 0:
                normalized = score / max_score
            else:
                normalized = 0
            
            if normalized > best_score:
                best_score = normalized
                best_match = p
        
        if not best_match or best_score < 0.5:
            return None, None
        
        # 根据结果倾向计算因子
        outcome = best_match['outcome']
        sample = best_match.get('sample', 3)
        
        # Wilson Score 置信下界（样本量修正）
        # 假设样本准确率 = 100%（因为都是连杰确认的模式）
        # 但用Wilson下界来修正小样本
        correct = sample  # 全部正确
        total = sample
        z = 1.96
        p_hat = correct / total if total > 0 else 0
        z2 = z * z
        center = p_hat + z2 / (2 * total)
        margin = z * math.sqrt((p_hat * (1 - p_hat) + z2 / (4 * total)) / total)
        wilson = (center - margin) / (1 + z2 / total)
        
        # Bayesian Average（先验：50%准确率，10场伪计数）
        bayesian = (10 * 0.50 + total * 1.0) / (10 + total)
        
        # 综合可信分
        trust = (wilson + bayesian) / 2
        
        # 可信分 → 因子
        if '胜' in outcome and '负' not in outcome and '平' not in outcome and '客负' not in outcome:
            # 明确指向胜 → 增加权重
            base_factor = 1.0 + trust * 0.5  # 1.0~1.5
        elif '负' in outcome or '客负' in outcome:
            # 明确指向负 → 降低权重（如果当前信号指向胜）
            base_factor = 1.0 - trust * 0.5  # 0.5~1.0
        elif '平' in outcome and '不' not in outcome:
            # 指向平 → 轻微调整
            base_factor = 1.0 - trust * 0.2  # 0.8~1.0
        elif '不' in outcome:
            # 指向不胜 → 中等调整
            base_factor = 1.0 - trust * 0.3  # 0.7~1.0
        else:
            base_factor = 1.0
        
        # 匹配度衰减：匹配度越低，因子越接近1.0
        final_factor = 1.0 + (base_factor - 1.0) * best_score
        
        return round(final_factor, 3), {
            'league': best_match['league'] or '通用',
            'pattern': f"欧赔{best_match['odds_change'] or ''} 亚盘{best_match['asian_line'] or ''}{best_match['asian_change'] or ''}",
            'outcome': outcome,
            'sample': sample,
            'trust': round(trust, 3),
            'match_score': round(best_score, 3),
            'factor': round(final_factor, 3),
            'note': best_match.get('note', ''),
        }
    
    def batch_match(self, matches):
        """批量匹配
        
        Args:
            matches: [{league, home_odds, away_odds, draw_odds, odds_change, asian_line, asian_change}, ...]
        
        Returns:
            [(factor, pattern), ...]
        """
        results = []
        for m in matches:
            factor, pattern = self.match(**m)
            results.append((factor, pattern))
        return results
    
    def get_stats(self):
        """获取模式库统计"""
        leagues = set()
        total_patterns = len(self.patterns)
        with_odds = sum(1 for p in self.patterns if p['odds_range'])
        with_asian = sum(1 for p in self.patterns if p['asian_line'])
        with_odds_change = sum(1 for p in self.patterns if p['odds_change'])
        
        for p in self.patterns:
            if p['league']:
                leagues.add(p['league'])
        
        return {
            'total_patterns': total_patterns,
            'leagues': sorted(leagues),
            'league_count': len(leagues),
            'with_odds_range': with_odds,
            'with_asian': with_asian,
            'with_odds_change': with_odds_change,
        }


# ===== 使用示例 =====
if __name__ == '__main__':
    engine = ExpertPatternEngine()
    
    stats = engine.get_stats()
    print(f'\n=== 专家模式库统计 ===\n')
    print(f'总模式数: {stats["total_patterns"]}')
    print(f'覆盖联赛: {", ".join(stats["leagues"])} ({stats["league_count"]}个)')
    print(f'含赔率范围: {stats["with_odds_range"]}条')
    print(f'含亚盘: {stats["with_asian"]}条')
    print(f'含欧赔变化: {stats["with_odds_change"]}条')
    
    # 测试匹配
    print(f'\n=== 测试匹配 ===\n')
    
    test_cases = [
        {'league': '法甲', 'home_odds': 1.85, 'asian_line': '半球', 'asian_change': '降', 'asian_to': '半球平'},
        {'league': '德甲', 'home_odds': 1.85, 'odds_change': '升降升'},
        {'league': '德甲', 'away_odds': 2.25},
        {'league': '意甲', 'away_odds': 2.25},
        {'league': '英超', 'away_odds': 5.5, 'odds_change': '降升升', 'asian_line': '让0.75', 'asian_change': '降'},
        {'league': '英超', 'asian_line': '半', 'asian_change': '升', 'asian_to': '半一'},
        {'league': '韩职', 'home_odds': 2.15, 'odds_change': '升降降'},
        {'league': '日乙', 'home_odds': 2.25},
        {'league': '荷兰', 'asian_line': '平半', 'asian_change': '升', 'asian_to': '半'},
        {'league': '葡萄牙', 'asian_line': '平半', 'asian_change': '升', 'asian_to': '半'},
        # 无匹配
        {'league': '西甲', 'home_odds': 3.5, 'odds_change': '不变不变不变'},
    ]
    
    for tc in test_cases:
        factor, pattern = engine.match(**tc)
        if pattern:
            print(f'✅ {tc["league"]} | 主{tc.get("home_odds","-")} 客{tc.get("away_odds","-")} | '
                  f'{pattern["pattern"]} → {pattern["outcome"]} | '
                  f'因子×{factor:.3f} (样本{pattern["sample"]}场, 可信{pattern["trust"]:.0%})')
        else:
            print(f'❌ {tc.get("league","")} | 无匹配')
