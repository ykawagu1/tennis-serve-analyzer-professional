#!/usr/bin/env python3
"""
テニスサーブ解析システムの評価基準分析
各技術要素の評価基準を分析し、より差が出やすい基準を提案する
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

class EvaluationCriteriaAnalyzer:
    """評価基準の分析クラス"""
    
    def __init__(self):
        # 現在の評価基準（推定値）
        self.current_criteria = {
            'knee_movement': {
                'ideal_range': (130, 150),  # 理想的な膝曲げ角度
                'scoring_bands': [
                    (170, float('inf'), -4.0),  # 大幅に浅い
                    (160, 170, -3.0),           # 浅い
                    (150, 160, -1.5),           # やや浅い
                    (130, 150, 0.0),            # 理想
                    (120, 130, -1.0),           # やや深い
                    (110, 120, -2.5),           # 深い
                    (0, 110, -4.0)              # 大幅に深い
                ]
            },
            'elbow_position': {
                'ideal_range': (-0.02, 0.05),  # 肩との相対位置
                'scoring_bands': [
                    (-float('inf'), -0.08, -4.0),  # 大幅に低い
                    (-0.08, -0.05, -2.5),          # 低い
                    (-0.05, -0.02, -1.0),          # やや低い
                    (-0.02, 0.05, 0.0),            # 理想
                    (0.05, 0.1, -1.0),             # やや高い
                    (0.1, 0.15, -2.5),             # 高い
                    (0.15, float('inf'), -4.0)     # 大幅に高い
                ]
            },
            'body_rotation': {
                'shoulder_ideal': (85, 95),     # 理想的な肩回転角度
                'hip_ideal': (40, 60),          # 理想的な腰回転角度
                'shoulder_bands': [
                    (0, 70, -4.0),              # 大幅不足
                    (70, 80, -2.5),             # 不足
                    (80, 85, -1.0),             # やや不足
                    (85, 95, 0.0),              # 理想
                    (95, 105, -1.5),            # やや過度
                    (105, float('inf'), -3.0)   # 過度
                ],
                'hip_bands': [
                    (0, 25, -4.0),              # 大幅不足
                    (25, 35, -2.5),             # 不足
                    (35, 40, -1.0),             # やや不足
                    (40, 60, 0.0),              # 理想
                    (60, 70, -1.5),             # やや過度
                    (70, float('inf'), -3.0)    # 過度
                ]
            },
            'toss_trajectory': {
                'height_ideal': (0.4, 0.6),    # 正規化された高さ
                'distance_ideal': (0.08, 0.15), # 前方距離
                'height_bands': [
                    (0, 0.2, -4.0),             # 大幅に低い
                    (0.2, 0.3, -3.0),           # 低い
                    (0.3, 0.4, -1.5),           # やや低い
                    (0.4, 0.6, 0.0),            # 理想
                    (0.6, 0.7, -1.0),           # やや高い
                    (0.7, 0.8, -2.5),           # 高い
                    (0.8, 1.0, -4.0)            # 大幅に高い
                ]
            }
        }
    
    def analyze_current_criteria(self):
        """現在の評価基準を分析"""
        print("🔍 === 現在の評価基準分析 ===")
        
        # 各技術要素の分析
        for category, criteria in self.current_criteria.items():
            self.analyze_category_criteria(category, criteria)
        
        # 問題点の特定
        self.identify_criteria_issues()
    
    def analyze_category_criteria(self, category: str, criteria: Dict):
        """カテゴリ別の評価基準分析"""
        jp_names = {
            'knee_movement': '膝の動き',
            'elbow_position': '肘の位置',
            'body_rotation': '体回転',
            'toss_trajectory': 'トス軌道'
        }
        
        print(f"\n📊 {jp_names.get(category, category)}:")
        
        if category == 'knee_movement':
            ideal_range = criteria['ideal_range']
            print(f"  理想範囲: {ideal_range[0]}°-{ideal_range[1]}°")
            print(f"  理想範囲の幅: {ideal_range[1] - ideal_range[0]}°")
            
            # スコア分布の計算
            test_angles = [100, 120, 135, 145, 160, 175]
            print(f"  テスト角度でのスコア:")
            for angle in test_angles:
                score = self.calculate_knee_score(angle, criteria)
                print(f"    {angle}°: {score:.1f}点")
        
        elif category == 'elbow_position':
            ideal_range = criteria['ideal_range']
            print(f"  理想範囲: {ideal_range[0]:.2f}-{ideal_range[1]:.2f}")
            
            test_positions = [-0.1, -0.03, 0.0, 0.03, 0.08, 0.12]
            print(f"  テスト位置でのスコア:")
            for pos in test_positions:
                score = self.calculate_elbow_score(pos, criteria)
                print(f"    {pos:.2f}: {score:.1f}点")
        
        elif category == 'body_rotation':
            print(f"  肩回転理想範囲: {criteria['shoulder_ideal'][0]}°-{criteria['shoulder_ideal'][1]}°")
            print(f"  腰回転理想範囲: {criteria['hip_ideal'][0]}°-{criteria['hip_ideal'][1]}°")
            
            test_rotations = [(60, 30), (80, 45), (90, 50), (100, 65), (120, 80)]
            print(f"  テスト回転でのスコア:")
            for shoulder, hip in test_rotations:
                score = self.calculate_rotation_score(shoulder, hip, criteria)
                print(f"    肩{shoulder}°/腰{hip}°: {score:.1f}点")
    
    def calculate_knee_score(self, angle: float, criteria: Dict) -> float:
        """膝角度からスコアを計算"""
        base_score = 10.0
        for min_val, max_val, penalty in criteria['scoring_bands']:
            if min_val <= angle < max_val:
                return base_score + penalty
        return base_score
    
    def calculate_elbow_score(self, position: float, criteria: Dict) -> float:
        """肘位置からスコアを計算"""
        base_score = 10.0
        for min_val, max_val, penalty in criteria['scoring_bands']:
            if min_val <= position < max_val:
                return base_score + penalty
        return base_score
    
    def calculate_rotation_score(self, shoulder: float, hip: float, criteria: Dict) -> float:
        """体回転からスコアを計算"""
        shoulder_score = 10.0
        hip_score = 10.0
        
        # 肩回転スコア
        for min_val, max_val, penalty in criteria['shoulder_bands']:
            if min_val <= shoulder < max_val:
                shoulder_score += penalty
                break
        
        # 腰回転スコア
        for min_val, max_val, penalty in criteria['hip_bands']:
            if min_val <= hip < max_val:
                hip_score += penalty
                break
        
        return (shoulder_score + hip_score) / 2
    
    def identify_criteria_issues(self):
        """評価基準の問題点を特定"""
        print(f"\n⚠️ 現在の評価基準の問題点:")
        
        issues = []
        
        # 1. 理想範囲が広すぎる問題
        knee_range = self.current_criteria['knee_movement']['ideal_range']
        knee_width = knee_range[1] - knee_range[0]
        if knee_width > 15:
            issues.append(f"膝の理想範囲が広すぎる ({knee_width}°)")
        
        # 2. 減点幅が小さすぎる問題
        max_penalty = 4.0
        if max_penalty < 5.0:
            issues.append(f"最大減点が小さすぎる ({max_penalty}点)")
        
        # 3. スコア分布の問題
        print(f"\n📈 スコア分布の問題:")
        print(f"  - 多くの動画が6-8点の狭い範囲に集中")
        print(f"  - 技術レベルの違いが総合スコアに反映されにくい")
        print(f"  - 理想範囲が広すぎて差が出にくい")
        
        return issues
    
    def propose_stricter_criteria(self):
        """より厳格な評価基準を提案"""
        print(f"\n🚀 より厳格な評価基準の提案:")
        
        stricter_criteria = {
            'knee_movement': {
                'ideal_range': (135, 145),  # 理想範囲を狭める
                'scoring_bands': [
                    (170, float('inf'), -6.0),  # 減点を増加
                    (160, 170, -4.5),
                    (150, 160, -2.5),
                    (145, 150, -1.0),
                    (135, 145, 0.0),            # 理想範囲を狭める
                    (125, 135, -1.5),
                    (115, 125, -3.5),
                    (0, 115, -6.0)              # 減点を増加
                ]
            },
            'elbow_position': {
                'ideal_range': (0.0, 0.03),    # 理想範囲を狭める
                'scoring_bands': [
                    (-float('inf'), -0.06, -6.0),  # 減点を増加
                    (-0.06, -0.03, -4.0),
                    (-0.03, 0.0, -1.5),
                    (0.0, 0.03, 0.0),              # 理想範囲を狭める
                    (0.03, 0.06, -2.0),
                    (0.06, 0.1, -4.0),
                    (0.1, float('inf'), -6.0)      # 減点を増加
                ]
            },
            'body_rotation': {
                'shoulder_ideal': (88, 92),     # 理想範囲を狭める
                'hip_ideal': (45, 55),          # 理想範囲を狭める
                'shoulder_bands': [
                    (0, 75, -6.0),              # 減点を増加
                    (75, 83, -4.0),
                    (83, 88, -2.0),
                    (88, 92, 0.0),              # 理想範囲を狭める
                    (92, 98, -2.5),
                    (98, float('inf'), -5.0)    # 減点を増加
                ],
                'hip_bands': [
                    (0, 30, -6.0),              # 減点を増加
                    (30, 40, -4.0),
                    (40, 45, -2.0),
                    (45, 55, 0.0),              # 理想範囲を狭める
                    (55, 65, -2.5),
                    (65, float('inf'), -5.0)    # 減点を増加
                ]
            },
            'toss_trajectory': {
                'height_ideal': (0.45, 0.55),  # 理想範囲を狭める
                'distance_ideal': (0.1, 0.13), # 理想範囲を狭める
                'height_bands': [
                    (0, 0.25, -6.0),            # 減点を増加
                    (0.25, 0.35, -4.5),
                    (0.35, 0.45, -2.5),
                    (0.45, 0.55, 0.0),          # 理想範囲を狭める
                    (0.55, 0.65, -2.0),
                    (0.65, 0.75, -4.0),
                    (0.75, 1.0, -6.0)           # 減点を増加
                ]
            }
        }
        
        # 新基準での効果予測
        self.predict_stricter_effects(stricter_criteria)
        
        return stricter_criteria
    
    def predict_stricter_effects(self, stricter_criteria: Dict):
        """厳格化の効果を予測"""
        print(f"\n📈 厳格化の効果予測:")
        
        # テストケース
        test_cases = [
            {
                'name': '上級者レベル',
                'knee_angle': 140,
                'elbow_pos': 0.02,
                'shoulder_rot': 90,
                'hip_rot': 50,
                'toss_height': 0.5
            },
            {
                'name': '中級者レベル',
                'knee_angle': 150,
                'elbow_pos': 0.05,
                'shoulder_rot': 85,
                'hip_rot': 45,
                'toss_height': 0.4
            },
            {
                'name': '初心者レベル',
                'knee_angle': 165,
                'elbow_pos': -0.05,
                'shoulder_rot': 75,
                'hip_rot': 35,
                'toss_height': 0.3
            }
        ]
        
        for case in test_cases:
            print(f"\n  {case['name']}:")
            
            # 現在の基準でのスコア
            current_knee = self.calculate_knee_score(case['knee_angle'], self.current_criteria['knee_movement'])
            current_elbow = self.calculate_elbow_score(case['elbow_pos'], self.current_criteria['elbow_position'])
            current_rotation = self.calculate_rotation_score(case['shoulder_rot'], case['hip_rot'], self.current_criteria['body_rotation'])
            
            # 新基準でのスコア
            strict_knee = self.calculate_knee_score(case['knee_angle'], stricter_criteria['knee_movement'])
            strict_elbow = self.calculate_elbow_score(case['elbow_pos'], stricter_criteria['elbow_position'])
            strict_rotation = self.calculate_rotation_score(case['shoulder_rot'], case['hip_rot'], stricter_criteria['body_rotation'])
            
            print(f"    膝: {current_knee:.1f} → {strict_knee:.1f} ({strict_knee-current_knee:+.1f})")
            print(f"    肘: {current_elbow:.1f} → {strict_elbow:.1f} ({strict_elbow-current_elbow:+.1f})")
            print(f"    回転: {current_rotation:.1f} → {strict_rotation:.1f} ({strict_rotation-current_rotation:+.1f})")
    
    def generate_criteria_modification_code(self, stricter_criteria: Dict):
        """評価基準修正用のコードを生成"""
        print(f"\n💻 評価基準修正コード:")
        
        # 膝の動き修正コード
        print("\n# 膝の動き評価の修正 (analyze_knee_movement):")
        print("```python")
        print("# より厳格な膝曲げ評価（理想: 135-145度）")
        print("if max_bend_angle > 170:")
        print("    depth_issues.append(\"膝の曲げが大幅に浅すぎます\")")
        print("    depth_score -= 6.0")
        print("elif max_bend_angle > 160:")
        print("    depth_issues.append(\"膝の曲げが浅すぎます\")")
        print("    depth_score -= 4.5")
        print("elif max_bend_angle > 150:")
        print("    depth_issues.append(\"膝の曲げがやや浅いです\")")
        print("    depth_score -= 2.5")
        print("elif max_bend_angle > 145:")
        print("    depth_issues.append(\"膝の曲げが少し浅いです\")")
        print("    depth_score -= 1.0")
        print("elif max_bend_angle < 115:")
        print("    depth_issues.append(\"膝の曲げが大幅に深すぎます\")")
        print("    depth_score -= 6.0")
        print("elif max_bend_angle < 125:")
        print("    depth_issues.append(\"膝の曲げが深すぎます\")")
        print("    depth_score -= 3.5")
        print("elif max_bend_angle < 135:")
        print("    depth_issues.append(\"膝の曲げがやや深いです\")")
        print("    depth_score -= 1.5")
        print("```")
        
        # 体回転修正コード
        print("\n# 体回転評価の修正 (analyze_body_rotation):")
        print("```python")
        print("# 肩の回転評価（理想: 88-92度）")
        print("if max_shoulder_rotation < 75:")
        print("    issues.append(\"肩の回転が大幅に不足しています\")")
        print("    shoulder_score -= 6.0")
        print("elif max_shoulder_rotation < 83:")
        print("    issues.append(\"肩の回転が不足しています\")")
        print("    shoulder_score -= 4.0")
        print("elif max_shoulder_rotation < 88:")
        print("    issues.append(\"肩の回転がやや不足しています\")")
        print("    shoulder_score -= 2.0")
        print("elif max_shoulder_rotation > 98:")
        print("    issues.append(\"肩の回転が過度です\")")
        print("    shoulder_score -= 5.0")
        print("elif max_shoulder_rotation > 92:")
        print("    issues.append(\"肩の回転がやや過度です\")")
        print("    shoulder_score -= 2.5")
        print("")
        print("# 腰の回転評価（理想: 45-55度）")
        print("if max_hip_rotation < 30:")
        print("    issues.append(\"腰の回転が大幅に不足しています\")")
        print("    hip_score -= 6.0")
        print("elif max_hip_rotation < 40:")
        print("    issues.append(\"腰の回転が不足しています\")")
        print("    hip_score -= 4.0")
        print("elif max_hip_rotation < 45:")
        print("    issues.append(\"腰の回転がやや不足しています\")")
        print("    hip_score -= 2.0")
        print("elif max_hip_rotation > 65:")
        print("    issues.append(\"腰の回転が過度です\")")
        print("    hip_score -= 5.0")
        print("elif max_hip_rotation > 55:")
        print("    issues.append(\"腰の回転がやや過度です\")")
        print("    hip_score -= 2.5")
        print("```")


def main():
    """メイン実行関数"""
    analyzer = EvaluationCriteriaAnalyzer()
    
    print("🎾 テニスサーブ解析システムの評価基準分析を開始します")
    
    # 現在の評価基準分析
    analyzer.analyze_current_criteria()
    
    # より厳格な基準の提案
    stricter_criteria = analyzer.propose_stricter_criteria()
    
    # 修正コードの生成
    analyzer.generate_criteria_modification_code(stricter_criteria)
    
    print("\n🎯 評価基準分析完了！より厳格な基準が提案されました。")


if __name__ == "__main__":
    main()

