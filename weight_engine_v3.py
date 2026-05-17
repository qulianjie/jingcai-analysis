# -*- coding: utf-8 -*-
"""
竞彩预测权重调整引擎 V3 - Wilson Score + Bayesian Average

解决当前算法的三个问题：
1. 不看样本量 → Wilson Score 置信区间
2. 只增不减 → 低准确率组合惩罚
3. 线性boost粗糙 → 非线性映射 + 分层修正

用法：
    from weight_engine_v3 import WeightEngine
    engine = WeightEngine('jingcai/learnings/learned_patterns_v2.json')
    adjusted_weights, logs, summary = engine.adjust_weights(base_weights, match_context)
"""
import json
import math
import os


class WeightEngine:
    """权重精细化调整引擎 V3"""
    
    def __init__(self, learned_patterns_path, z=1.96, prior_strength=10, prior_mean=0.50):
        """
        Args:
            learned_patterns_path: learned_patterns_v2.json 路径
            z: Wilson Score 置信度参数（1.96=95%, 1.645=90%）
            prior_strength: 贝叶斯先验强度（伪计数），建议10
            prior_mean: 贝叶斯先验均值（全局平均准确率），建议0.50
        """
        self.z = z
        self.prior_strength = prior_strength
        self.prior_mean = prior_mean
        
        if not os.path.exists(learned_patterns_path):
            print(f'[WEIGHT-ENGINE] 警告: 学习文件不存在: {learned_patterns_path}')
            self.learned = {}
        else:
            with open(learned_patterns_path, 'r', encoding='utf-8') as f:
                self.learned = json.load(f)
        
        # 预计算所有模式的可信度
        self._precompute()
    
    def _precompute(self):
        """预计算所有模式的可信度"""
        self.combo_trust = []
        self.league_trust = []
        self.dim_trust = []
        self.conf_adjust = {}
        
        # 1. 组合模式（高准确率）
        for combo in self.learned.get('high_accuracy_combos', []):
            correct = combo['correct']
            total = combo['total']
            wilson = self.wilson(correct, total)
            bayesian = self.bayesian_avg(correct, total)
            trust = (wilson + bayesian) / 2  # 综合评分
            self.combo_trust.append({
                'tag': combo['tag'],
                'wilson': wilson,
                'bayesian': bayesian,
                'trust': trust,
                'accuracy': correct / total if total > 0 else 0,
                'n': total,
                'factor': self.trust_to_factor(trust),
                'is_low': False,
            })
        
        # 2. 组合模式（低准确率）
        for combo in self.learned.get('low_accuracy_combos', []):
            correct = combo['correct']
            total = combo['total']
            wilson = self.wilson(correct, total)
            bayesian = self.bayesian_avg(correct, total)
            trust = (wilson + bayesian) / 2
            self.combo_trust.append({
                'tag': combo['tag'],
                'wilson': wilson,
                'bayesian': bayesian,
                'trust': trust,
                'accuracy': correct / total if total > 0 else 0,
                'n': total,
                'factor': self.trust_to_factor(trust),
                'is_low': True,
            })
        
        # 3. 联赛准确率
        for lr in self.learned.get('league_accuracy', []):
            correct = lr.get('correct', 0)
            total = lr.get('total', 0)
            wilson = self.wilson(correct, total)
            bayesian = self.bayesian_avg(correct, total)
            trust = (wilson + bayesian) / 2
            self.league_trust.append({
                'league': lr['league'],
                'wilson': wilson,
                'bayesian': bayesian,
                'trust': trust,
                'accuracy': lr.get('accuracy', 0),
                'n': total,
                'factor': self.trust_to_factor(trust),
            })
        
        # 4. 维度准确率（盘路匹配度）
        for pa in self.learned.get('panlu_accuracy', []):
            correct = pa.get('correct', 0)
            total = pa.get('total', 0)
            wilson = self.wilson(correct, total)
            bayesian = self.bayesian_avg(correct, total)
            trust = (wilson + bayesian) / 2
            self.dim_trust.append({
                'level': pa['level'],
                'wilson': wilson,
                'bayesian': bayesian,
                'trust': trust,
                'accuracy': pa.get('accuracy', 0),
                'n': total,
                'factor': self.trust_to_factor(trust),
            })
        
        # 5. 信心度修正
        for conf, data in self.learned.get('confidence_adjust', {}).items():
            self.conf_adjust[conf] = data
        
        print(f'[WEIGHT-ENGINE] 已加载: {len(self.combo_trust)} 组合模式, '
              f'{len(self.league_trust)} 联赛, {len(self.dim_trust)} 维度')
    
    def wilson(self, correct, total):
        """
        Wilson Score 置信下界
        
        公式：
        Wilson下界 = (p + z²/(2n) - z×√((p(1-p)+z²/(4n))/n)) / (1 + z²/n)
        
        效果：
        - 80%准确率, 5场  → Wilson下界 33.2%  (样本少, 不敢信)
        - 80%准确率, 20场 → Wilson下界 59.7%  (样本适中)
        - 80%准确率, 100场 → Wilson下界 72.2% (样本充足)
        - 0%准确率, 11场   → Wilson下界 0.0%   (全错就是全错)
        """
        if total == 0:
            return 0.0
        
        p = correct / total
        z2 = self.z ** 2
        
        center = p + z2 / (2 * total)
        margin = self.z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)
        denominator = 1 + z2 / total
        
        return (center - margin) / denominator
    
    def bayesian_avg(self, correct, total):
        """
        Bayesian Average 平滑评分
        
        公式：
        Bayesian评分 = (C × m + n × p) / (C + n)
        
        其中：
        - C = prior_strength (伪计数, 默认10)
        - m = prior_mean (先验均值, 默认0.50)
        - n = 样本量
        - p = 实际准确率
        
        效果：
        - 80%准确率, 5场  → 55.6%  (被先验拉回)
        - 80%准确率, 20场 → 66.7%  (逐渐接近实际)
        - 80%准确率, 100场 → 76.9% (基本信任实际值)
        """
        if total == 0:
            return self.prior_mean
        
        p = correct / total
        return (self.prior_strength * self.prior_mean + total * p) / (self.prior_strength + total)
    
    def trust_to_factor(self, trust_score):
        """
        综合可信分 → 权重修正系数
        
        映射规则：
        - trust ≥ 0.60 → 1.0x ~ 1.5x  (高可信, 增加权重)
        - 0.40 ≤ trust < 0.60 → 1.0x   (中等, 不调整)
        - 0.20 ≤ trust < 0.40 → 0.8x ~ 1.0x (偏低, 轻微惩罚)
        - 0.0 ≤ trust < 0.20  → 0.3x ~ 0.8x (很低, 强惩罚)
        - trust = 0.0         → 0.0x    (零可信, 完全忽略)
        """
        if trust_score >= 0.60:
            # 高可信: 线性插值 0.60→1.0x, 0.80→1.5x
            return 1.0 + min(0.5, (trust_score - 0.60) / 0.40 * 0.5)
        elif trust_score >= 0.40:
            # 中等: 不调整
            return 1.0
        elif trust_score >= 0.20:
            # 偏低: 线性插值 0.20→0.8x, 0.40→1.0x
            return 0.8 + (trust_score - 0.20) / 0.20 * 0.2
        elif trust_score > 0.0:
            # 很低: 线性插值 0.0→0.3x, 0.20→0.8x
            return 0.3 + (trust_score / 0.20) * 0.5
        else:
            return 0.0
    
    def extract_tags(self, match_context):
        """从比赛上下文中提取标签"""
        tags = []
        
        league = match_context.get('league', '')
        if league:
            tags.append(f'联赛:{league}')
        
        macau_line = match_context.get('macau_line', '')
        if macau_line:
            tags.append(f'澳门亚盘:{macau_line}')
        
        asian_dir = match_context.get('asian_dir', '')
        if asian_dir:
            tags.append(f'亚盘:{asian_dir}')
        
        oupei_dir = match_context.get('oupei_dir', '')
        if oupei_dir:
            tags.append(f'欧赔:{oupei_dir}')
        
        rangqiu_dir = match_context.get('rangqiu_dir', '')
        if rangqiu_dir:
            tags.append(f'让球:{rangqiu_dir}')
        
        baijia_dir = match_context.get('baijia_dir', '')
        if baijia_dir:
            tags.append(f'百家:{baijia_dir}')
        
        zhuangjia_dir = match_context.get('zhuangjia_dir', '')
        if zhuangjia_dir:
            tags.append(f'庄家:{zhuangjia_dir}')
        
        betting_ratio = match_context.get('betting_ratio', '')
        if betting_ratio:
            tags.append(f'投注占比:{betting_ratio}')
        
        confidence = match_context.get('confidence_level', '')
        if confidence:
            tags.append(f'信心:{confidence}')
        
        return tags
    
    def match_combos(self, tags):
        """
        匹配组合模式
        
        精确匹配: 组合中所有标签都在 tags 中
        返回按精度排序的结果（四维 > 三维 > 二维 > 一维）
        """
        results = []
        
        for combo in self.combo_trust:
            tag = combo['tag']
            parts = [p.strip() for p in tag.split('×')]
            
            # 检查所有部分是否都在 tags 中
            all_matched = all(part in tags for part in parts)
            
            if all_matched:
                results.append({
                    'tag': tag,
                    'factor': combo['factor'],
                    'trust': combo['trust'],
                    'wilson': combo['wilson'],
                    'bayesian': combo['bayesian'],
                    'accuracy': combo['accuracy'],
                    'n': combo['n'],
                    'is_low': combo.get('is_low', False),
                    'precision': len(parts),
                })
        
        # 按精度排序: 四维 > 三维 > 二维 > 一维, 同精度按可信度排序
        results.sort(key=lambda x: (-x['precision'], -x['trust']))
        
        return results
    
    def match_league(self, tags):
        """匹配联赛准确率"""
        league_tag = None
        for tag in tags:
            if tag.startswith('联赛:'):
                league_tag = tag
                break
        
        if not league_tag:
            return None
        
        league_name = league_tag.split(':', 1)[1]
        
        for lr in self.league_trust:
            if league_name in lr['league']:
                return lr
        
        return None
    
    def parse_combo_dims(self, tag):
        """从组合标签解析涉及的维度"""
        dims = []
        
        dim_keywords = {
            '竞彩': '竞彩同赔',
            'IWC': 'IW同赔',
            'IW': 'IW同赔',
            '盘路': '盘路匹配',
            '澳门': '澳门亚盘',
            '亚盘': '澳门亚盘',
            '让球': '让球同赔',
            '主队': '主队主场',
            '主场': '主队主场',
            '客队': '客队客场',
            '客场': '客队客场',
            '百家': '百家对比',
            '庄家': '庄家盈亏',
            '投注': '投注占比',
            '盈亏占比': '盈亏占比',
            '欧赔': '欧赔趋势',
        }
        
        for keyword, dim_name in dim_keywords.items():
            if keyword in tag and dim_name not in dims:
                dims.append(dim_name)
        
        # 排除不属于权重的标签
        exclude = ['信心度', '投注占比', '盈亏占比']
        dims = [d for d in dims if d not in exclude]
        
        return dims if dims else ['欧赔趋势']  # 默认影响欧赔趋势
    
    def adjust_weights(self, base_weights, match_context):
        """
        主入口: 调整权重
        
        Args:
            base_weights: 基础权重列表 [(name, score, weight), ...]
            match_context: 比赛上下文 {league, macau_line, asian_dir, ...}
        
        Returns:
            adjusted: 调整后的权重列表
            logs: 调整日志
            summary: 调整摘要
        """
        # 1. 提取标签
        tags = self.extract_tags(match_context)
        
        # 2. 匹配组合模式
        combo_matches = self.match_combos(tags)
        
        # 3. 匹配联赛
        league_match = self.match_league(tags)
        
        # 4. 计算调整因子（分层）
        factors = {}  # {维度名: 因子}
        logs = []
        
        # ===== 优先级1: 组合模式 =====
        if combo_matches:
            best_combo = combo_matches[0]
            matched_dims = self.parse_combo_dims(best_combo['tag'])
            
            if best_combo['is_low']:
                # 低准确率: 降低匹配维度权重
                factor = best_combo['factor']
                for dim in matched_dims:
                    factors[dim] = factor
                    logs.append(
                        f'[LOW-COMBO] {best_combo["tag"]}: '
                        f'trust={best_combo["trust"]:.3f}, '
                        f'wilson={best_combo["wilson"]:.3f}, '
                        f'bayesian={best_combo["bayesian"]:.3f}, '
                        f'accuracy={best_combo["accuracy"]:.0%}({best_combo["n"]}场), '
                        f'{dim} ×{factor:.2f}'
                    )
            else:
                # 高准确率: 提高匹配维度权重
                factor = best_combo['factor']
                for dim in matched_dims:
                    current_factor = factors.get(dim, 1.0)
                    factors[dim] = max(current_factor, factor)
                    logs.append(
                        f'[HIGH-COMBO] {best_combo["tag"]}: '
                        f'trust={best_combo["trust"]:.3f}, '
                        f'wilson={best_combo["wilson"]:.3f}, '
                        f'bayesian={best_combo["bayesian"]:.3f}, '
                        f'accuracy={best_combo["accuracy"]:.0%}({best_combo["n"]}场), '
                        f'{dim} ×{factor:.2f}'
                    )
        
        # ===== 优先级2: 联赛准确率 =====
        if league_match:
            league_factor = league_match['factor']
            logs.append(
                f'[LEAGUE] {league_match["league"]}: '
                f'trust={league_match["trust"]:.3f}, '
                f'wilson={league_match["wilson"]:.3f}, '
                f'bayesian={league_match["bayesian"]:.3f}, '
                f'accuracy={league_match["accuracy"]:.0%}({league_match["n"]}场), '
                f'all dims ×{league_factor:.2f}'
            )
            
            # 对所有有明确方向的维度应用联赛修正
            for i, (name, score, weight) in enumerate(base_weights):
                if abs(score) > 0.1:
                    current_factor = factors.get(name, 1.0)
                    factors[name] = current_factor * league_factor
        
        # ===== 优先级3: 信心度修正 =====
        confidence = match_context.get('confidence_level', '')
        if confidence and confidence in self.conf_adjust:
            adj = self.conf_adjust[confidence]
            adj_factor = adj.get('adjust_factor', 1.0)
            logs.append(
                f'[CONF] {confidence}: 实际{adj.get("accuracy", 0):.0%}, '
                f'修正系数×{adj_factor:.2f}'
            )
        
        # ===== 应用调整 =====
        adjusted = []
        for name, score, weight in base_weights:
            factor = factors.get(name, 1.0)
            new_weight = weight * factor
            # 限制范围: 5% ~ 30%
            new_weight = max(0.05, min(0.30, new_weight))
            adjusted.append((name, score, new_weight))
        
        # ===== 归一化 =====
        total_weight = sum(w for _, _, w in adjusted)
        if total_weight > 0:
            adjusted = [(name, score, w / total_weight) for name, score, w in adjusted]
        
        # 5. 计算调整摘要
        summary = {
            'tags_matched': tags,
            'combo_matches': combo_matches[:3],
            'league_match': league_match,
            'final_weights': {name: round(w, 4) for name, _, w in adjusted},
            'weight_changes': {},
        }
        
        for (name, _, new_w), (_, _, old_w) in zip(adjusted, base_weights):
            if abs(new_w - old_w) > 0.001:
                summary['weight_changes'][name] = {
                    'old': round(old_w, 4),
                    'new': round(new_w, 4),
                    'delta': round(new_w - old_w, 4),
                }
        
        return adjusted, logs, summary


# ===== 使用示例 =====
if __name__ == '__main__':
    import sys
    
    # 路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    learned_path = os.path.join(script_dir, 'learnings', 'learned_patterns_v2.json')
    
    if not os.path.exists(learned_path):
        print(f'错误: 学习文件不存在: {learned_path}')
        sys.exit(1)
    
    # 初始化引擎
    engine = WeightEngine(learned_path)
    
    # 演示 Wilson Score 效果
    print('\n=== Wilson Score 效果演示 ===\n')
    print(f'{"准确率":<8} {"样本量":<8} {"Wilson下界":<12} {"Bayesian":<10} {"综合":<8} {"因子":<6}')
    print('-' * 60)
    
    test_cases = [
        (0.80, 5),
        (0.80, 10),
        (0.80, 20),
        (0.80, 100),
        (0.60, 200),
        (0.00, 11),
        (1.00, 3),
    ]
    
    for acc, n in test_cases:
        correct = int(acc * n)
        w = engine.wilson(correct, n)
        b = engine.bayesian_avg(correct, n)
        trust = (w + b) / 2
        factor = engine.trust_to_factor(trust)
        print(f'{acc:<8.0%} {n:<8} {w:<12.3f} {b:<10.3f} {trust:<8.3f} {factor:<6.2f}x')
    
    # 模拟一场日职比赛
    print('\n\n=== 权重调整演示 ===\n')
    
    base_weights = [
        ('欧赔趋势', 0.3, 0.10),
        ('竞彩同赔', 0.2, 0.12),
        ('IW同赔', -0.1, 0.10),
        ('澳门亚盘', 0.5, 0.10),
        ('让球同赔', 0.0, 0.10),
        ('主队主场', 0.4, 0.12),
        ('客队客场', 0.1, 0.12),
        ('百家对比', -0.2, 0.10),
        ('庄家盈亏', 0.0, 0.04),
    ]
    
    match_context = {
        'league': '日职',
        'macau_line': '半球',
        'asian_dir': '利好客',
        'oupei_dir': '利好主',
        'rangqiu_dir': '利好客',
        'baijia_dir': '利好客',
        'zhuangjia_dir': '客胜',
        'betting_ratio': '高',
        'confidence_level': '高',
    }
    
    print('比赛上下文:')
    for k, v in match_context.items():
        print(f'  {k}: {v}')
    
    adjusted, logs, summary = engine.adjust_weights(base_weights, match_context)
    
    print('\n--- 调整日志 ---')
    for log in logs:
        print(log)
    
    print('\n--- 权重变化 ---')
    changes = summary.get('weight_changes', {})
    if not changes:
        print('  (无变化)')
    else:
        for name, change in changes.items():
            arrow = '↑' if change['delta'] > 0 else '↓'
            print(f'  {name}: {change["old"]:.4f} → {change["new"]:.4f} ({arrow}{abs(change["delta"]):.4f})')
    
    print('\n--- 最终权重 ---')
    for name, score, weight in adjusted:
        bar = '█' * int(weight * 100)
        print(f'  {name:10s}: {weight:.4f} {bar}')
