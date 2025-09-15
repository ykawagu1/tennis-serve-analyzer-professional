#!/usr/bin/env python3
"""
テニスサーブ解析システムのスコアリング分析
現在の重み設定と評価基準を分析し、改善案を提案する
"""

import numpy as np
import matplotlib.pyplot as plt
import json
from typing import Dict, List, Tuple

class ScoringAnalyzer:
    """スコアリングシステムの分析クラス"""
    
    def __init__(self):
        # 現在の重み設定
        self.current_weights = {
            'knee_movement': 0.10,      # 膝の動き（基礎）
            'elbow_position': 0.15,     # 肘の位置（重要）
            'toss_trajectory': 0.15,    # トス軌道（重要）
            'body_rotation': 0.25,      # 体回転（最重要）
            'timing': 0.10,             # タイミング（基礎）
            'follow_through': 0.25      # フォロースルー（最重要）
        }
        
        # 技術レベル別の期待スコア範囲
        self.skill_levels = {
            'beginner': {'range': (3.0, 5.5), 'description': '初心者'},
            'intermediate': {'range': (5.5, 7.5), 'description': '中級者'},
            'advanced': {'range': (7.5, 9.0), 'description': '上級者'},
            'professional': {'range': (9.0, 10.0), 'description': 'プロ'}
        }
    
    def analyze_current_system(self):
        """現在のシステムの分析"""
        print("🔍 === 現在のスコアリングシステム分析 ===")
        
        # 重み配分の分析
        print(f"\n📊 重み配分:")
        total_weight = sum(self.current_weights.values())
        print(f"合計重み: {total_weight:.2f}")
        
        for category, weight in sorted(self.current_weights.items(), key=lambda x: x[1], reverse=True):
            percentage = (weight / total_weight) * 100
            print(f"  {category}: {weight:.2f} ({percentage:.1f}%)")
        
        # 重み配分の可視化
        self.visualize_weights()
        
        # スコア分布の分析
        self.analyze_score_distribution()
        
        # 問題点の特定
        self.identify_issues()
    
    def visualize_weights(self):
        """重み配分の可視化"""
        categories = list(self.current_weights.keys())
        weights = list(self.current_weights.values())
        
        # 日本語カテゴリ名
        jp_categories = {
            'knee_movement': '膝の動き',
            'elbow_position': '肘の位置',
            'toss_trajectory': 'トス軌道',
            'body_rotation': '体回転',
            'timing': 'タイミング',
            'follow_through': 'フォロースルー'
        }
        
        jp_labels = [jp_categories[cat] for cat in categories]
        
        plt.figure(figsize=(10, 6))
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']
        
        plt.pie(weights, labels=jp_labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('現在の重み配分', fontsize=14, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig('/home/ubuntu/current_weights.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 重み配分グラフを保存: /home/ubuntu/current_weights.png")
    
    def analyze_score_distribution(self):
        """スコア分布の分析"""
        print(f"\n📈 スコア分布分析:")
        
        # 様々なスコア組み合わせでの総合スコア計算
        test_scenarios = [
            {'name': '完璧なサーブ', 'scores': [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]},
            {'name': '上級者サーブ', 'scores': [9.0, 8.5, 8.0, 9.5, 8.0, 9.0]},
            {'name': '中級者サーブ', 'scores': [7.0, 7.0, 6.5, 7.5, 6.0, 7.0]},
            {'name': '初心者サーブ', 'scores': [5.0, 4.5, 4.0, 5.5, 4.0, 5.0]},
            {'name': '問題のあるサーブ', 'scores': [3.0, 3.5, 3.0, 4.0, 3.0, 3.5]},
            {'name': '現在の動画1', 'scores': [7.0, 6.75, 6.15, 7.0, 6.46, 7.65]},  # 推定値
            {'name': '現在の動画2', 'scores': [7.0, 8.0, 4.24, 7.0, 6.78, 7.75]}   # 推定値
        ]
        
        for scenario in test_scenarios:
            total_score = self.calculate_weighted_score(scenario['scores'])
            print(f"  {scenario['name']}: {total_score:.2f}点")
        
        # スコア感度分析
        self.analyze_score_sensitivity()
    
    def calculate_weighted_score(self, scores: List[float]) -> float:
        """重み付きスコアの計算"""
        categories = list(self.current_weights.keys())
        total_score = 0.0
        
        for i, category in enumerate(categories):
            if i < len(scores):
                total_score += scores[i] * self.current_weights[category]
        
        return total_score
    
    def analyze_score_sensitivity(self):
        """スコア感度分析"""
        print(f"\n🎯 スコア感度分析:")
        
        # ベースラインスコア（中級者レベル）
        baseline_scores = [7.0, 7.0, 6.5, 7.5, 6.0, 7.0]
        baseline_total = self.calculate_weighted_score(baseline_scores)
        
        print(f"ベースライン総合スコア: {baseline_total:.2f}点")
        
        # 各カテゴリで1点改善した場合の影響
        categories = list(self.current_weights.keys())
        jp_categories = {
            'knee_movement': '膝の動き',
            'elbow_position': '肘の位置',
            'toss_trajectory': 'トス軌道',
            'body_rotation': '体回転',
            'timing': 'タイミング',
            'follow_through': 'フォロースルー'
        }
        
        print(f"\n各カテゴリで1点改善した場合の総合スコア変化:")
        for i, category in enumerate(categories):
            improved_scores = baseline_scores.copy()
            improved_scores[i] += 1.0
            improved_total = self.calculate_weighted_score(improved_scores)
            impact = improved_total - baseline_total
            
            print(f"  {jp_categories[category]}: +{impact:.3f}点 (重み: {self.current_weights[category]:.2f})")
    
    def identify_issues(self):
        """現在のシステムの問題点特定"""
        print(f"\n⚠️ 現在のシステムの問題点:")
        
        issues = []
        
        # 重み配分の問題
        max_weight = max(self.current_weights.values())
        min_weight = min(self.current_weights.values())
        weight_ratio = max_weight / min_weight
        
        if weight_ratio < 3.0:
            issues.append(f"重み配分の差が小さすぎる (最大/最小 = {weight_ratio:.1f})")
        
        # 技術的重要度と重み配分の不一致
        technical_importance = {
            'body_rotation': 0.30,      # インパクト時の体回転は最重要
            'follow_through': 0.25,     # フォロースルーも重要
            'elbow_position': 0.20,     # 肘の位置は技術差が出やすい
            'toss_trajectory': 0.15,    # トスは基礎だが重要
            'knee_movement': 0.05,      # 膝は基礎的
            'timing': 0.05              # タイミングは他の要素に含まれる
        }
        
        print(f"\n💡 理想的な重み配分との比較:")
        for category in self.current_weights.keys():
            current = self.current_weights[category]
            ideal = technical_importance[category]
            diff = current - ideal
            
            jp_name = {
                'knee_movement': '膝の動き',
                'elbow_position': '肘の位置',
                'toss_trajectory': 'トス軌道',
                'body_rotation': '体回転',
                'timing': 'タイミング',
                'follow_through': 'フォロースルー'
            }[category]
            
            status = "適正" if abs(diff) < 0.03 else ("過大" if diff > 0 else "過小")
            print(f"  {jp_name}: 現在{current:.2f} vs 理想{ideal:.2f} ({status})")
        
        return issues
    
    def propose_improvements(self):
        """改善案の提案"""
        print(f"\n🚀 改善案:")
        
        # 新しい重み配分の提案
        improved_weights = {
            'knee_movement': 0.05,      # 膝の動き（基礎）- さらに削減
            'elbow_position': 0.20,     # 肘の位置（重要）- 増加
            'toss_trajectory': 0.15,    # トス軌道（重要）- 維持
            'body_rotation': 0.30,      # 体回転（最重要）- 増加
            'timing': 0.05,             # タイミング（基礎）- さらに削減
            'follow_through': 0.25      # フォロースルー（最重要）- 維持
        }
        
        print(f"\n📊 提案する新しい重み配分:")
        for category, weight in sorted(improved_weights.items(), key=lambda x: x[1], reverse=True):
            current = self.current_weights[category]
            change = weight - current
            
            jp_name = {
                'knee_movement': '膝の動き',
                'elbow_position': '肘の位置',
                'toss_trajectory': 'トス軌道',
                'body_rotation': '体回転',
                'timing': 'タイミング',
                'follow_through': 'フォロースルー'
            }[category]
            
            change_str = f"({change:+.2f})" if change != 0 else ""
            print(f"  {jp_name}: {weight:.2f} {change_str}")
        
        # 改善効果の予測
        self.predict_improvement_effects(improved_weights)
        
        return improved_weights
    
    def predict_improvement_effects(self, new_weights: Dict[str, float]):
        """改善効果の予測"""
        print(f"\n📈 改善効果の予測:")
        
        # テストケース
        test_cases = [
            {'name': '技術差の大きい2つのサーブ', 
             'scores1': [6.0, 6.0, 5.0, 6.0, 5.0, 6.0],  # 低技術
             'scores2': [8.0, 9.0, 8.0, 9.0, 8.0, 9.0]}, # 高技術
            {'name': '現在の2つの動画（推定）',
             'scores1': [7.0, 6.75, 6.15, 7.0, 6.46, 7.65],
             'scores2': [7.0, 8.0, 4.24, 7.0, 6.78, 7.75]}
        ]
        
        for case in test_cases:
            print(f"\n  {case['name']}:")
            
            # 現在の重みでの計算
            current_score1 = self.calculate_weighted_score_with_weights(case['scores1'], self.current_weights)
            current_score2 = self.calculate_weighted_score_with_weights(case['scores2'], self.current_weights)
            current_diff = abs(current_score2 - current_score1)
            
            # 新しい重みでの計算
            new_score1 = self.calculate_weighted_score_with_weights(case['scores1'], new_weights)
            new_score2 = self.calculate_weighted_score_with_weights(case['scores2'], new_weights)
            new_diff = abs(new_score2 - new_score1)
            
            print(f"    現在の重み: {current_score1:.2f} vs {current_score2:.2f} (差: {current_diff:.2f})")
            print(f"    新しい重み: {new_score1:.2f} vs {new_score2:.2f} (差: {new_diff:.2f})")
            print(f"    差の変化: {new_diff - current_diff:+.2f}")
    
    def calculate_weighted_score_with_weights(self, scores: List[float], weights: Dict[str, float]) -> float:
        """指定された重みでスコアを計算"""
        categories = list(weights.keys())
        total_score = 0.0
        
        for i, category in enumerate(categories):
            if i < len(scores):
                total_score += scores[i] * weights[category]
        
        return total_score
    
    def generate_weight_modification_code(self, new_weights: Dict[str, float]):
        """重み修正用のコードを生成"""
        print(f"\n💻 motion_analyzer.py の修正コード:")
        print("```python")
        print("def calculate_overall_score(self, analysis_results: Dict) -> float:")
        print('    """総合スコアの計算"""')
        print("    scores = []")
        print("    weights = {")
        
        for category, weight in new_weights.items():
            comment = {
                'knee_movement': '膝の動き（基礎）',
                'elbow_position': '肘の位置（重要）',
                'toss_trajectory': 'トス軌道（重要）',
                'body_rotation': '体回転（最重要）',
                'timing': 'タイミング（基礎）',
                'follow_through': 'フォロースルー（最重要）'
            }[category]
            
            print(f"        '{category}': {weight:.2f},      # {comment}")
        
        print("    }")
        print("")
        print("    for category, weight in weights.items():")
        print("        if category in analysis_results:")
        print("            category_score = analysis_results[category].get('overall_score', 0.0)")
        print("            scores.append(category_score * weight)")
        print("")
        print("    return sum(scores) if scores else 0.0")
        print("```")


def main():
    """メイン実行関数"""
    analyzer = ScoringAnalyzer()
    
    print("🎾 テニスサーブ解析システムのスコアリング分析を開始します")
    
    # 現在のシステム分析
    analyzer.analyze_current_system()
    
    # 改善案の提案
    improved_weights = analyzer.propose_improvements()
    
    # 修正コードの生成
    analyzer.generate_weight_modification_code(improved_weights)
    
    print("\n🎯 分析完了！改善案が提案されました。")


if __name__ == "__main__":
    main()


