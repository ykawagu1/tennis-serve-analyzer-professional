"""
フォロースルー解析モジュール

テニスサーブのフォロースルーフェーズに特化した解析を行います。
タイミング評価ではなく、実際のフォロースルー技術を評価します。
"""

import numpy as np
from typing import List, Dict, Optional


class FollowThroughAnalyzer:
    """フォロースルー解析クラス"""
    
    def analyze_follow_through(self, pose_results: List[Dict], serve_phases: List) -> Dict:
        """
        フォロースルーの解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            フォロースルー解析結果
        """
        # フォロースルーフェーズを特定
        follow_through_phase = next((p for p in serve_phases if 'follow' in p.name.lower()), None)
        
        if not follow_through_phase:
            return self._create_fallback_result()
        
        # フォロースルー期間のフレームを抽出
        start_frame = follow_through_phase.start_frame
        end_frame = follow_through_phase.end_frame
        follow_through_frames = pose_results[start_frame:end_frame + 1]
        
        # 各評価要素を分析
        swing_completion = self._analyze_swing_completion(follow_through_frames)
        body_rotation_completion = self._analyze_body_rotation_completion(follow_through_frames)
        balance_maintenance = self._analyze_balance_maintenance(follow_through_frames)
        racket_path = self._analyze_racket_path(follow_through_frames)
        
        # 総合スコア計算
        overall_score = self._calculate_follow_through_score(
            swing_completion, body_rotation_completion, balance_maintenance, racket_path
        )
        
        return {
            'swing_completion': swing_completion,
            'body_rotation_completion': body_rotation_completion,
            'balance_maintenance': balance_maintenance,
            'racket_path': racket_path,
            'overall_score': overall_score,
            'issues': self._collect_issues(swing_completion, body_rotation_completion, balance_maintenance, racket_path),
            'recommendations': self._get_follow_through_recommendations(overall_score)
        }
    
    def _analyze_swing_completion(self, frames: List[Dict]) -> Dict:
        """ラケットの振り抜き完成度を分析"""
        right_wrist_positions = []
        
        for frame in frames:
            if frame.get('has_pose') and 'right_wrist' in frame.get('landmarks', {}):
                right_wrist_positions.append(frame['landmarks']['right_wrist'])
        
        if len(right_wrist_positions) < 3:
            return {'score': 5.0, 'completion_rate': 0.5, 'issue': '振り抜きデータ不足'}
        
        # 振り抜きの軌道を分析
        start_pos = right_wrist_positions[0]
        end_pos = right_wrist_positions[-1]
        
        # 左側への移動距離（振り抜きの指標）
        horizontal_movement = end_pos['x'] - start_pos['x']
        vertical_movement = start_pos['y'] - end_pos['y']  # 上から下への移動
        
        # 振り抜き完成度の評価
        completion_score = 10.0
        
        if horizontal_movement < 0.1:  # 左への移動が不足
            completion_score -= 3.0
        elif horizontal_movement < 0.15:
            completion_score -= 1.5
        
        if vertical_movement < 0.05:  # 下への移動が不足
            completion_score -= 2.0
        elif vertical_movement < 0.1:
            completion_score -= 1.0
        
        completion_rate = min(1.0, (horizontal_movement + vertical_movement) / 0.3)
        
        return {
            'score': max(0.0, completion_score),
            'completion_rate': completion_rate,
            'horizontal_movement': horizontal_movement,
            'vertical_movement': vertical_movement
        }
    
    def _analyze_body_rotation_completion(self, frames: List[Dict]) -> Dict:
        """体の回転完了度を分析"""
        shoulder_angles = []
        
        for frame in frames:
            if frame.get('has_pose'):
                landmarks = frame.get('landmarks', {})
                left_shoulder = landmarks.get('left_shoulder')
                right_shoulder = landmarks.get('right_shoulder')
                
                if left_shoulder and right_shoulder:
                    angle = self._calculate_rotation_angle(left_shoulder, right_shoulder)
                    shoulder_angles.append(angle)
        
        if not shoulder_angles:
            return {'score': 5.0, 'rotation_completion': 0.5, 'issue': '回転データ不足'}
        
        # 回転の完了度を評価
        final_rotation = shoulder_angles[-1] if shoulder_angles else 0
        max_rotation = max(shoulder_angles) if shoulder_angles else 0
        
        completion_score = 10.0
        
        # 最終的な回転角度の評価（理想: 120度以上）
        if final_rotation < 100:
            completion_score -= 3.0
        elif final_rotation < 110:
            completion_score -= 1.5
        
        # 回転の一貫性評価
        rotation_consistency = self._calculate_rotation_consistency(shoulder_angles)
        if rotation_consistency < 0.7:
            completion_score -= 2.0
        
        return {
            'score': max(0.0, completion_score),
            'final_rotation': final_rotation,
            'max_rotation': max_rotation,
            'rotation_consistency': rotation_consistency
        }
    
    def _analyze_balance_maintenance(self, frames: List[Dict]) -> Dict:
        """バランス維持を分析"""
        left_ankle_positions = []
        right_ankle_positions = []
        
        for frame in frames:
            if frame.get('has_pose'):
                landmarks = frame.get('landmarks', {})
                if 'left_ankle' in landmarks:
                    left_ankle_positions.append(landmarks['left_ankle'])
                if 'right_ankle' in landmarks:
                    right_ankle_positions.append(landmarks['right_ankle'])
        
        if len(left_ankle_positions) < 3 or len(right_ankle_positions) < 3:
            return {'score': 5.0, 'stability': 0.5, 'issue': 'バランスデータ不足'}
        
        # 足の安定性を評価
        left_stability = self._calculate_position_stability(left_ankle_positions)
        right_stability = self._calculate_position_stability(right_ankle_positions)
        
        balance_score = 10.0
        avg_stability = (left_stability + right_stability) / 2
        
        if avg_stability < 0.6:
            balance_score -= 4.0
        elif avg_stability < 0.75:
            balance_score -= 2.0
        elif avg_stability < 0.85:
            balance_score -= 1.0
        
        return {
            'score': max(0.0, balance_score),
            'left_stability': left_stability,
            'right_stability': right_stability,
            'overall_stability': avg_stability
        }
    
    def _analyze_racket_path(self, frames: List[Dict]) -> Dict:
        """ラケットの軌道を分析"""
        right_wrist_positions = []
        
        for frame in frames:
            if frame.get('has_pose') and 'right_wrist' in frame.get('landmarks', {}):
                right_wrist_positions.append(frame['landmarks']['right_wrist'])
        
        if len(right_wrist_positions) < 3:
            return {'score': 5.0, 'path_quality': 0.5, 'issue': '軌道データ不足'}
        
        # 軌道の滑らかさを評価
        path_smoothness = self._calculate_trajectory_smoothness(right_wrist_positions)
        
        # 理想的な軌道パターンとの比較
        path_score = 10.0
        
        if path_smoothness < 0.6:
            path_score -= 3.0
        elif path_smoothness < 0.75:
            path_score -= 1.5
        
        return {
            'score': max(0.0, path_score),
            'path_smoothness': path_smoothness,
            'path_quality': path_smoothness
        }
    
    def _calculate_follow_through_score(self, swing_completion: Dict, body_rotation: Dict, 
                                      balance: Dict, racket_path: Dict) -> float:
        """フォロースルー総合スコアを計算"""
        weights = {
            'swing_completion': 0.3,
            'body_rotation': 0.25,
            'balance': 0.25,
            'racket_path': 0.2
        }
        
        total_score = (
            swing_completion['score'] * weights['swing_completion'] +
            body_rotation['score'] * weights['body_rotation'] +
            balance['score'] * weights['balance'] +
            racket_path['score'] * weights['racket_path']
        )
        
        return total_score
    
    def _collect_issues(self, swing_completion: Dict, body_rotation: Dict, 
                       balance: Dict, racket_path: Dict) -> List[str]:
        """問題点を収集"""
        issues = []
        
        if swing_completion['score'] < 7.0:
            issues.append("ラケットの振り抜きが不完全です")
        
        if body_rotation['score'] < 7.0:
            issues.append("体の回転が不完全です")
        
        if balance['score'] < 7.0:
            issues.append("バランスの維持に問題があります")
        
        if racket_path['score'] < 7.0:
            issues.append("ラケットの軌道が不安定です")
        
        return issues
    
    def _get_follow_through_recommendations(self, overall_score: float) -> List[str]:
        """改善提案を生成"""
        recommendations = []
        
        if overall_score < 6.0:
            recommendations.extend([
                "フォロースルーの基本動作を見直しましょう",
                "ラケットを体の左側まで完全に振り抜く練習をしましょう",
                "体の回転を最後まで完了させる意識を持ちましょう"
            ])
        elif overall_score < 8.0:
            recommendations.extend([
                "フォロースルーの完成度を高めましょう",
                "バランスを保ちながらの振り抜きを練習しましょう"
            ])
        else:
            recommendations.append("フォロースルーは良好です。この調子を維持しましょう")
        
        return recommendations
    
    def _create_fallback_result(self) -> Dict:
        """フォールバック結果を作成"""
        return {
            'swing_completion': {'score': 5.0, 'completion_rate': 0.5},
            'body_rotation_completion': {'score': 5.0, 'rotation_completion': 0.5},
            'balance_maintenance': {'score': 5.0, 'stability': 0.5},
            'racket_path': {'score': 5.0, 'path_quality': 0.5},
            'overall_score': 5.0,
            'issues': ['フォロースルーフェーズが特定できませんでした'],
            'recommendations': ['フォロースルーの基本動作を確認しましょう']
        }
    
    # ヘルパーメソッド
    def _calculate_rotation_angle(self, left_point: Dict, right_point: Dict) -> float:
        """2点から回転角度を計算"""
        dx = right_point['x'] - left_point['x']
        dy = right_point['y'] - left_point['y']
        angle = np.arctan2(dy, dx) * 180 / np.pi
        return abs(angle)
    
    def _calculate_rotation_consistency(self, angles: List[float]) -> float:
        """回転の一貫性を計算"""
        if len(angles) < 2:
            return 0.5
        
        # 角度変化の標準偏差を計算
        angle_changes = [abs(angles[i+1] - angles[i]) for i in range(len(angles)-1)]
        std_dev = np.std(angle_changes)
        
        # 一貫性スコア（標準偏差が小さいほど高い）
        consistency = max(0.0, 1.0 - std_dev / 30.0)
        return consistency
    
    def _calculate_position_stability(self, positions: List[Dict]) -> float:
        """位置の安定性を計算"""
        if len(positions) < 2:
            return 0.5
        
        # 位置変化の標準偏差を計算
        x_positions = [pos['x'] for pos in positions]
        y_positions = [pos['y'] for pos in positions]
        
        x_std = np.std(x_positions)
        y_std = np.std(y_positions)
        
        # 安定性スコア（標準偏差が小さいほど高い）
        stability = max(0.0, 1.0 - (x_std + y_std) / 0.2)
        return stability
    
    def _calculate_trajectory_smoothness(self, positions: List[Dict]) -> float:
        """軌道の滑らかさを計算"""
        if len(positions) < 3:
            return 0.5
        
        # 軌道の曲率変化を計算
        curvature_changes = []
        
        for i in range(1, len(positions) - 1):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            next_pos = positions[i+1]
            
            # ベクトルの角度変化を計算
            v1 = np.array([curr_pos['x'] - prev_pos['x'], curr_pos['y'] - prev_pos['y']])
            v2 = np.array([next_pos['x'] - curr_pos['x'], next_pos['y'] - curr_pos['y']])
            
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle_change = np.arccos(cos_angle)
                curvature_changes.append(angle_change)
        
        if not curvature_changes:
            return 0.5
        
        # 滑らかさスコア（角度変化が小さいほど高い）
        avg_curvature = np.mean(curvature_changes)
        smoothness = max(0.0, 1.0 - avg_curvature / np.pi)
        
        return smoothness

