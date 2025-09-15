"""
テニスサービス動作解析 - 動作解析サービス
ポーズ検出結果からテニスサービス特有の動作を解析
"""

import numpy as np
import math
import time
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from .follow_through_analyzer import FollowThroughAnalyzer


@dataclass
class ServePhase:
    """サーブフェーズの定義"""
    name: str
    start_frame: int
    end_frame: int
    duration: float
    key_events: List[str]


class MotionAnalyzer:
    """テニスサービス動作解析クラス"""
    
    def __init__(self):
        """動作解析器の初期化"""
        self.serve_phases = [
            'preparation',      # 準備フェーズ
            'ball_toss',       # ボールトス
            'trophy_position', # トロフィーポジション
            'acceleration',    # 加速フェーズ
            'contact',         # ボール接触
            'follow_through'   # フォロースルー
        ]
        
        # フォロースルー専用解析器を初期化
        self.follow_through_analyzer = FollowThroughAnalyzer()
        
        # 各フェーズの特徴的な動作パターン
        self.phase_characteristics = {
            'preparation': {
                'description': '構えから動作開始まで',
                'key_landmarks': ['left_shoulder', 'right_shoulder', 'left_wrist', 'right_wrist'],
                'motion_patterns': ['静止状態', '軽微な準備動作']
            },
            'ball_toss': {
                'description': 'ボールトスの実行',
                'key_landmarks': ['left_wrist', 'right_wrist', 'left_shoulder'],
                'motion_patterns': ['左手の上昇', '右手の後方移動開始']
            },
            'trophy_position': {
                'description': 'トロフィーポジション形成',
                'key_landmarks': ['right_elbow', 'right_wrist', 'left_wrist', 'right_shoulder'],
                'motion_patterns': ['右肘の高い位置', '左手の最高点到達']
            },
            'acceleration': {
                'description': '加速フェーズ',
                'key_landmarks': ['right_wrist', 'right_elbow', 'right_shoulder'],
                'motion_patterns': ['右手の急激な加速', '体重移動']
            },
            'contact': {
                'description': 'ボール接触',
                'key_landmarks': ['right_wrist', 'right_elbow'],
                'motion_patterns': ['最高到達点での接触', '最大速度']
            },
            'follow_through': {
                'description': 'フォロースルー',
                'key_landmarks': ['right_wrist', 'right_elbow', 'left_foot', 'right_foot'],
                'motion_patterns': ['右手の下降', '着地動作']
            }
        }
    
    def analyze_serve_motion(self, pose_results: List[Dict]) -> Dict:
        """
        サーブ動作の包括的解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            
        Returns:
            動作解析結果の辞書
        """
        print(f"=== 動作解析開始 ===")
        print(f"入力データ: {len(pose_results)} フレーム")
        
        if not pose_results:
            raise ValueError("ポーズ検出結果が空です")
        
        # ポーズが検出されたフレームの確認
        detected_frames = [result for result in pose_results if result.get('has_pose', False)]
        
        print(f"ポーズ検出フレーム数: {len(detected_frames)}/{len(pose_results)}")
        
        # サンプルデータの確認
        if pose_results:
            sample_frame = pose_results[0]
            print(f"サンプルフレーム構造: {list(sample_frame.keys())}")
            if 'landmarks' in sample_frame:
                print(f"ランドマーク数: {len(sample_frame['landmarks'])}")
                print(f"ランドマーク例: {list(sample_frame['landmarks'].keys())[:5]}")
        
        if len(detected_frames) < 10:  # 最低10フレームは必要
            print("⚠️ ポーズ検出フレーム数が不足 - エラー結果を返す")
            return {
                'analysis_id': f"analysis_{int(time.time() * 1000)}",
                'video_metadata': self._extract_video_metadata(pose_results),
                'serve_phases': {},
                'technical_analysis': {
                    'knee_movement': {'overall_score': 0.0, 'issues': ['ポーズ検出不足'], 'recommendations': ['動画品質を改善してください']},
                    'elbow_position': {'overall_score': 0.0, 'issues': ['ポーズ検出不足'], 'recommendations': ['より明確に人体が映る動画を使用してください']},
                    'toss_trajectory': {'overall_score': 0.0, 'issues': ['ポーズ検出不足'], 'recommendations': ['照明条件を改善してください']},
                    'body_rotation': {'overall_score': 0.0, 'issues': ['ポーズ検出不足'], 'recommendations': ['カメラアングルを調整してください']},
                    'timing': {'overall_score': 0.0, 'issues': ['ポーズ検出不足'], 'recommendations': ['動画の解像度を上げてください']}
                },
                'overall_score': 0.0,
                'recommendations': ['ポーズ検出が不十分です。動画品質を改善して再度お試しください。']
            }
        
        # サーブフェーズの特定
        serve_phases = self.identify_serve_phases(pose_results)
        
        # 各技術要素の解析
        print("=== 技術解析開始 ===")
        knee_analysis = self.analyze_knee_movement(pose_results, serve_phases)
        print(f"膝解析完了: スコア = {knee_analysis.get('overall_score', 'N/A')}")
        
        elbow_analysis = self.analyze_elbow_position(pose_results, serve_phases)
        print(f"肘解析完了: スコア = {elbow_analysis.get('overall_score', 'N/A')}")
        
        toss_analysis = self.analyze_toss_trajectory(pose_results, serve_phases)
        print(f"トス解析完了: スコア = {toss_analysis.get('overall_score', 'N/A')}")
        
        body_rotation_analysis = self.analyze_body_rotation(pose_results, serve_phases)
        print(f"体回転解析完了: スコア = {body_rotation_analysis.get('overall_score', 'N/A')}")
        
        timing_analysis = self.analyze_timing(pose_results, serve_phases)
        print(f"タイミング解析完了: スコア = {timing_analysis.get('overall_score', 'N/A')}")
        
        # フォロースルー解析を追加
        follow_through_analysis = self.follow_through_analyzer.analyze_follow_through(pose_results, serve_phases)
        print(f"フォロースルー解析完了: スコア = {follow_through_analysis.get('overall_score', 'N/A')}")
        
        # 総合スコア計算
        print("=== 総合スコア計算開始 ===")
        analysis_dict = {
            'knee_movement': knee_analysis,
            'elbow_position': elbow_analysis,
            'toss_trajectory': toss_analysis,
            'body_rotation': body_rotation_analysis,
            'timing': timing_analysis,
            'follow_through': follow_through_analysis
        }
        
        for category, result in analysis_dict.items():
            print(f"{category}: {result.get('overall_score', 'N/A')}")
        
        overall_score = self.calculate_overall_score(analysis_dict)
        print(f"総合スコア計算完了: {overall_score}")
        
        return {
            'analysis_id': f"analysis_{int(pose_results[0].get('timestamp', time.time()) * 1000)}",
            'video_metadata': self._extract_video_metadata(pose_results),
            'serve_phases': {phase.name: {
                'start_frame': phase.start_frame,
                'end_frame': phase.end_frame,
                'duration': phase.duration,
                'key_events': phase.key_events
            } for phase in serve_phases},
            'technical_analysis': {
                'knee_movement': knee_analysis,
                'elbow_position': elbow_analysis,
                'toss_trajectory': toss_analysis,
                'body_rotation': body_rotation_analysis,
                'timing': timing_analysis,
                'follow_through': follow_through_analysis
            },
            'overall_score': overall_score,
            'recommendations': self._generate_recommendations({
                'knee_movement': knee_analysis,
                'elbow_position': elbow_analysis,
                'toss_trajectory': toss_analysis,
                'body_rotation': body_rotation_analysis,
                'timing': timing_analysis,
                'follow_through': follow_through_analysis
            })
        }
    
    def identify_serve_phases(self, pose_results: List[Dict]) -> List[ServePhase]:
        """
        サーブフェーズの自動特定
        
        Args:
            pose_results: ポーズ検出結果リスト
            
        Returns:
            特定されたサーブフェーズのリスト
        """
        phases = []
        total_frames = len(pose_results)
        
        print(f"=== フェーズ特定開始 ===")
        print(f"総フレーム数: {total_frames}")
        
        # 右手首の軌道を分析してフェーズを特定
        right_wrist_trajectory = self._extract_landmark_trajectory(pose_results, 'right_wrist')
        left_wrist_trajectory = self._extract_landmark_trajectory(pose_results, 'left_wrist')
        
        print(f"右手首軌道データ数: {len([t for t in right_wrist_trajectory if t is not None])}/{len(right_wrist_trajectory)}")
        print(f"左手首軌道データ数: {len([t for t in left_wrist_trajectory if t is not None])}/{len(left_wrist_trajectory)}")
        
        if not right_wrist_trajectory or not left_wrist_trajectory:
            print("⚠️ 手首軌道データが不足 - フォールバック処理を実行")
            print(f"right_wrist_trajectory存在: {bool(right_wrist_trajectory)}")
            print(f"left_wrist_trajectory存在: {bool(left_wrist_trajectory)}")
            # フォールバック: 均等分割
            return self._create_fallback_phases(total_frames)
        
        # 有効なデータポイントの確認
        valid_right_wrist = [t for t in right_wrist_trajectory if t is not None]
        valid_left_wrist = [t for t in left_wrist_trajectory if t is not None]
        
        print(f"有効な右手首データ: {len(valid_right_wrist)}")
        print(f"有効な左手首データ: {len(valid_left_wrist)}")
        
        if len(valid_right_wrist) < 10 or len(valid_left_wrist) < 10:
            print("⚠️ 有効なデータポイントが不足 - フォールバック処理を実行")
            print(f"右手首: {len(valid_right_wrist)} < 10? {len(valid_right_wrist) < 10}")
            print(f"左手首: {len(valid_left_wrist)} < 10? {len(valid_left_wrist) < 10}")
            return self._create_fallback_phases(total_frames)
        
        print("✅ 有効データ数チェック通過 - 実際のフェーズ特定を開始")
        
        try:
            # 左手首の最高点を検出（トス頂点）
            left_wrist_heights = [point['y'] for point in left_wrist_trajectory if point is not None]
            if left_wrist_heights:
                toss_peak_frame = np.argmin(left_wrist_heights)  # y座標が小さいほど高い
                print(f"トス頂点フレーム: {toss_peak_frame}")
            else:
                toss_peak_frame = total_frames // 3
                print(f"トス頂点フレーム（デフォルト）: {toss_peak_frame}")
            
            # 右手首の最高点を検出（接触点）
            right_wrist_heights = [point['y'] for point in right_wrist_trajectory if point is not None]
            if right_wrist_heights:
                contact_frame = np.argmin(right_wrist_heights)
                print(f"接触フレーム: {contact_frame}")
            else:
                contact_frame = total_frames * 2 // 3
                print(f"接触フレーム（デフォルト）: {contact_frame}")
            
            # フェーズ境界の推定
            preparation_end = max(1, toss_peak_frame - 20)
            ball_toss_end = toss_peak_frame + 5
            trophy_position_end = contact_frame - 10
            acceleration_end = contact_frame + 2
            contact_end = contact_frame + 5
            
            print(f"フェーズ境界: prep={preparation_end}, toss={ball_toss_end}, trophy={trophy_position_end}, accel={acceleration_end}, contact={contact_end}")
            
            # フェーズオブジェクトの作成
            fps = 30  # デフォルトFPS（実際の値があれば使用）
            
            phases = [
                ServePhase(
                    name='preparation',
                    start_frame=0,
                    end_frame=preparation_end,
                    duration=(preparation_end - 0) / fps,
                    key_events=['stance_setup', 'initial_position']
                ),
                ServePhase(
                    name='ball_toss',
                    start_frame=preparation_end,
                    end_frame=ball_toss_end,
                    duration=(ball_toss_end - preparation_end) / fps,
                    key_events=['toss_initiation', 'ball_release']
                ),
                ServePhase(
                    name='trophy_position',
                    start_frame=ball_toss_end,
                    end_frame=trophy_position_end,
                    duration=(trophy_position_end - ball_toss_end) / fps,
                    key_events=['trophy_formation', 'weight_transfer']
                ),
                ServePhase(
                    name='acceleration',
                    start_frame=trophy_position_end,
                    end_frame=acceleration_end,
                    duration=(acceleration_end - trophy_position_end) / fps,
                    key_events=['racket_acceleration', 'kinetic_chain']
                ),
                ServePhase(
                    name='contact',
                    start_frame=acceleration_end,
                    end_frame=contact_end,
                    duration=(contact_end - acceleration_end) / fps,
                    key_events=['ball_contact', 'maximum_reach']
                ),
                ServePhase(
                    name='follow_through',
                    start_frame=contact_end,
                    end_frame=total_frames - 1,
                    duration=(total_frames - 1 - contact_end) / fps,
                    key_events=['deceleration', 'landing']
                )
            ]
            
            print(f"✅ フェーズ特定完了: {len(phases)}個のフェーズを生成")
            return phases
            
        except Exception as e:
            print(f"⚠️ フェーズ特定中にエラー発生: {e}")
            import traceback
            traceback.print_exc()
            print("フォールバック処理を実行")
            return self._create_fallback_phases(total_frames)
    
    def analyze_knee_movement(self, pose_results: List[Dict], serve_phases: List[ServePhase]) -> Dict:
        """
        膝の動きの解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            膝の動き解析結果
        """
        print("=== 膝解析開始 ===")
        left_knee_trajectory = self._extract_landmark_trajectory(pose_results, 'left_knee')
        right_knee_trajectory = self._extract_landmark_trajectory(pose_results, 'right_knee')
        left_hip_trajectory = self._extract_landmark_trajectory(pose_results, 'left_hip')
        right_hip_trajectory = self._extract_landmark_trajectory(pose_results, 'right_hip')
        
        # 膝の角度計算（大腿部と下腿部の角度）
        knee_angles = []
        valid_angle_count = 0
        for i, result in enumerate(pose_results):
            if result['has_pose']:
                # 右膝の角度計算（右股関節-右膝-右足首）
                right_hip = result.get('landmarks', {}).get('right_hip')
                right_knee = result.get('landmarks', {}).get('right_knee')
                right_ankle = result.get('landmarks', {}).get('right_ankle')
                
                if i == 22:  # 異常値が出たフレーム22をデバッグ
                    print(f"フレーム {i} デバッグ:")
                    print(f"  right_hip: {right_hip}")
                    print(f"  right_knee: {right_knee}")
                    print(f"  right_ankle: {right_ankle}")
                
                right_angle = self._calculate_joint_angle(right_hip, right_knee, right_ankle)
                knee_angles.append(right_angle)
                
                if right_angle is not None:
                    valid_angle_count += 1
                    if i < 5 or i == 22:  # 最初の5フレームと異常値フレームをログ出力
                        print(f"フレーム {i}: 膝角度 = {right_angle:.1f}度")
            else:
                knee_angles.append(None)
        
        print(f"膝角度計算: 有効データ {valid_angle_count}/{len(pose_results)} フレーム")
        
        # 最大膝曲げの検出
        valid_angles = [angle for angle in knee_angles if angle is not None]
        if valid_angles:
            max_bend_angle = min(valid_angles)  # 角度が小さいほど曲がっている
            max_bend_frame = knee_angles.index(max_bend_angle)
            print(f"最大膝曲げ: {max_bend_angle:.1f}度 (フレーム {max_bend_frame})")
        else:
            max_bend_angle = 180
            max_bend_frame = 0
            print("⚠️ 有効な膝角度データなし - デフォルト値使用")
        
        # 膝曲げのタイミング評価
        trophy_phase = next((p for p in serve_phases if p.name == 'trophy_position'), None)
        timing_score = 10.0
        timing_issues = []
        
        if trophy_phase:
            print(f"トロフィーフェーズ: {trophy_phase.start_frame}-{trophy_phase.end_frame}")
            if max_bend_frame < trophy_phase.start_frame:
                timing_issues.append("膝の曲げが早すぎます")
                timing_score -= 2.0
            elif max_bend_frame > trophy_phase.end_frame:
                timing_issues.append("膝の曲げが遅すぎます")
                timing_score -= 2.0
        else:
            print("⚠️ トロフィーフェーズが見つかりません")
        
        # 膝曲げの深さ評価（厳格化された基準）
        depth_score = 10.0
        depth_issues = []
        
        # より厳格な膝曲げ評価（理想: 135-145度）
        if max_bend_angle > 170:
            depth_issues.append("膝の曲げが大幅に浅すぎます")
            depth_score -= 6.0
        elif max_bend_angle > 160:
            depth_issues.append("膝の曲げが浅すぎます")
            depth_score -= 4.5
        elif max_bend_angle > 150:
            depth_issues.append("膝の曲げがやや浅いです")
            depth_score -= 2.5
        elif max_bend_angle > 145:
            depth_issues.append("膝の曲げが少し浅いです")
            depth_score -= 1.0
        elif max_bend_angle < 115:
            depth_issues.append("膝の曲げが大幅に深すぎます")
            depth_score -= 6.0
        elif max_bend_angle < 125:
            depth_issues.append("膝の曲げが深すぎます")
            depth_score -= 3.5
        elif max_bend_angle < 135:
            depth_issues.append("膝の曲げがやや深いです")
            depth_score -= 1.5
        
        overall_knee_score = (timing_score + depth_score) / 2
        
        print(f"膝解析完了: timing={timing_score:.1f}, depth={depth_score:.1f}, overall={overall_knee_score:.1f}")
        
        return {
            'max_bend_angle': max_bend_angle,
            'max_bend_frame': max_bend_frame,
            'timing_score': timing_score,
            'depth_score': depth_score,
            'overall_score': overall_knee_score,
            'issues': timing_issues + depth_issues,
            'recommendations': self._get_knee_recommendations(max_bend_angle, timing_issues, depth_issues)
        }
    
    def analyze_elbow_position(self, pose_results: List[Dict], serve_phases: List[ServePhase]) -> Dict:
        """
        肘の位置の解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            肘の位置解析結果
        """
        right_elbow_trajectory = self._extract_landmark_trajectory(pose_results, 'right_elbow')
        right_shoulder_trajectory = self._extract_landmark_trajectory(pose_results, 'right_shoulder')
        
        # トロフィーポジション時の肘の高さを評価
        trophy_phase = next((p for p in serve_phases if p.name == 'trophy_position'), None)
        
        if trophy_phase and right_elbow_trajectory and right_shoulder_trajectory:
            trophy_frames = range(trophy_phase.start_frame, trophy_phase.end_frame + 1)
            
            # トロフィーポジション期間中の肘と肩の相対位置
            elbow_heights = []
            shoulder_heights = []
            
            for frame_idx in trophy_frames:
                if (frame_idx < len(right_elbow_trajectory) and 
                    frame_idx < len(right_shoulder_trajectory) and
                    right_elbow_trajectory[frame_idx] is not None and
                    right_shoulder_trajectory[frame_idx] is not None):
                    
                    elbow_heights.append(right_elbow_trajectory[frame_idx]['y'])
                    shoulder_heights.append(right_shoulder_trajectory[frame_idx]['y'])
            
            if elbow_heights and shoulder_heights:
                avg_elbow_height = np.mean(elbow_heights)
                avg_shoulder_height = np.mean(shoulder_heights)
                elbow_shoulder_diff = avg_shoulder_height - avg_elbow_height  # 正の値なら肘が肩より高い
            else:
                avg_elbow_height = 0.5
                avg_shoulder_height = 0.5
                elbow_shoulder_diff = 0
        else:
            avg_elbow_height = 0.5
            avg_shoulder_height = 0.5
            elbow_shoulder_diff = 0
        
        # 肘の高さ評価（厳格化された基準）
        height_score = 10.0
        height_issues = []
        
        # より厳格な肘の位置評価（理想: 0.0-0.03）
        if elbow_shoulder_diff < -0.06:  # 肘が肩より6%以上低い
            height_issues.append("肘の位置が大幅に低すぎます")
            height_score -= 6.0
        elif elbow_shoulder_diff < -0.03:  # 肘が肩より3%以上低い
            height_issues.append("肘の位置が低すぎます")
            height_score -= 4.0
        elif elbow_shoulder_diff < 0.0:  # 肘が肩より低い
            height_issues.append("肘の位置がやや低いです")
            height_score -= 1.5
        elif elbow_shoulder_diff > 0.1:  # 肘が肩より10%以上高い
            height_issues.append("肘の位置が大幅に高すぎます")
            height_score -= 6.0
        elif elbow_shoulder_diff > 0.06:  # 肘が肩より6%以上高い
            height_issues.append("肘の位置が高すぎます")
            height_score -= 4.0
        elif elbow_shoulder_diff > 0.03:  # 肘が肩より3%以上高い
            height_issues.append("肘の位置がやや高いです")
            height_score -= 2.0
        
        # 肘の安定性評価（厳格化）
        stability_score = 10.0
        if right_elbow_trajectory:
            trajectory_smoothness = self._calculate_trajectory_smoothness(right_elbow_trajectory)
            if trajectory_smoothness < 0.6:
                height_issues.append("肘の動きが大幅に不安定です")
                stability_score -= 4.0
            elif trajectory_smoothness < 0.7:
                height_issues.append("肘の動きが不安定です")
                stability_score -= 2.5
            elif trajectory_smoothness < 0.8:
                height_issues.append("肘の動きがやや不安定です")
                stability_score -= 1.0
        
        overall_elbow_score = (height_score + stability_score) / 2
        
        return {
            'average_height': avg_elbow_height,
            'shoulder_relative_position': elbow_shoulder_diff,
            'height_score': height_score,
            'stability_score': stability_score,
            'overall_score': overall_elbow_score,
            'issues': height_issues,
            'recommendations': self._get_elbow_recommendations(elbow_shoulder_diff, height_issues)
        }
    
    def analyze_toss_trajectory(self, pose_results: List[Dict], serve_phases: List[ServePhase]) -> Dict:
        """
        トスの軌道解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            トス軌道解析結果
        """
        left_wrist_trajectory = self._extract_landmark_trajectory(pose_results, 'left_wrist')
        
        if not left_wrist_trajectory:
            return {
                'max_height': 0.0,
                'forward_distance': 0.0,
                'consistency_score': 0.0,
                'overall_score': 0.0,
                'issues': ["トス軌道を検出できませんでした"],
                'recommendations': ["動画の品質を確認してください"]
            }
        
        # トスフェーズの特定
        toss_phase = next((p for p in serve_phases if p.name == 'ball_toss'), None)
        
        if toss_phase:
            toss_frames = range(toss_phase.start_frame, toss_phase.end_frame + 1)
            toss_trajectory = [left_wrist_trajectory[i] for i in toss_frames 
                             if i < len(left_wrist_trajectory) and left_wrist_trajectory[i] is not None]
        else:
            toss_trajectory = [point for point in left_wrist_trajectory if point is not None]
        
        if not toss_trajectory:
            return {
                'max_height': 0.0,
                'forward_distance': 0.0,
                'consistency_score': 0.0,
                'overall_score': 0.0,
                'issues': ["トス軌道データが不足しています"],
                'recommendations': ["より明確にトス動作を撮影してください"]
            }
        
        # トスの最高点
        heights = [point['y'] for point in toss_trajectory]
        max_height = min(heights)  # y座標が小さいほど高い
        max_height_normalized = 1.0 - max_height  # 正規化された高さ
        
        # トスの前方距離
        start_x = toss_trajectory[0]['x']
        end_x = toss_trajectory[-1]['x']
        forward_distance = abs(end_x - start_x)
        
        # トスの一貫性（軌道の滑らかさ）
        consistency_score = self._calculate_trajectory_smoothness(toss_trajectory)
        
        # 評価（厳格化された基準）
        height_score = 10.0
        distance_score = 10.0
        issues = []
        
        # 高さ評価（厳格化）
        if max_height_normalized < 0.2:
            issues.append("トスが大幅に低すぎます")
            height_score -= 4.0
        elif max_height_normalized < 0.3:
            issues.append("トスが低すぎます")
            height_score -= 3.0
        elif max_height_normalized < 0.4:
            issues.append("トスがやや低いです")
            height_score -= 1.5
        elif max_height_normalized > 0.8:
            issues.append("トスが大幅に高すぎます")
            height_score -= 4.0
        elif max_height_normalized > 0.7:
            issues.append("トスが高すぎます")
            height_score -= 2.5
        elif max_height_normalized > 0.6:
            issues.append("トスがやや高いです")
            height_score -= 1.0
        
        # 前方距離評価（厳格化）
        if forward_distance < 0.03:
            issues.append("トスの前方への投げが大幅に不足しています")
            distance_score -= 4.0
        elif forward_distance < 0.05:
            issues.append("トスの前方への投げが不足しています")
            distance_score -= 2.5
        elif forward_distance < 0.08:
            issues.append("トスの前方への投げがやや不足しています")
            distance_score -= 1.0
        elif forward_distance > 0.25:
            issues.append("トスが大幅に前方に行きすぎています")
            distance_score -= 4.0
        elif forward_distance > 0.2:
            issues.append("トスが前方に行きすぎています")
            distance_score -= 2.5
        elif forward_distance > 0.15:
            issues.append("トスがやや前方に行きすぎています")
            distance_score -= 1.0
        
        # 一貫性評価（厳格化）
        consistency_penalty = 0.0
        if consistency_score < 0.5:
            issues.append("トスの軌道が大幅に不安定です")
            consistency_penalty = 4.0
        elif consistency_score < 0.6:
            issues.append("トスの軌道が不安定です")
            consistency_penalty = 2.5
        elif consistency_score < 0.7:
            issues.append("トスの軌道がやや不安定です")
            consistency_penalty = 1.0
        
        overall_toss_score = (height_score + distance_score + consistency_score * 10) / 3
        
        return {
            'max_height': max_height_normalized,
            'forward_distance': forward_distance,
            'consistency_score': consistency_score,
            'height_score': height_score,
            'distance_score': distance_score,
            'overall_score': overall_toss_score,
            'issues': issues,
            'recommendations': self._get_toss_recommendations(max_height_normalized, forward_distance, issues)
        }
    
    def analyze_body_rotation(self, pose_results: List[Dict], serve_phases: List[ServePhase]) -> Dict:
        """
        体の回転の解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            体の回転解析結果
        """
        shoulder_rotations = []
        hip_rotations = []
        
        for result in pose_results:
            if result['has_pose']:
                landmarks = result.get('landmarks', {})
                
                # 肩の回転角度計算
                left_shoulder = landmarks.get('left_shoulder')
                right_shoulder = landmarks.get('right_shoulder')
                
                if left_shoulder and right_shoulder:
                    shoulder_angle = self._calculate_rotation_angle(left_shoulder, right_shoulder)
                    shoulder_rotations.append(shoulder_angle)
                else:
                    shoulder_rotations.append(None)
                
                # 腰の回転角度計算
                left_hip = landmarks.get('left_hip')
                right_hip = landmarks.get('right_hip')
                
                if left_hip and right_hip:
                    hip_angle = self._calculate_rotation_angle(left_hip, right_hip)
                    hip_rotations.append(hip_angle)
                else:
                    hip_rotations.append(None)
            else:
                shoulder_rotations.append(None)
                hip_rotations.append(None)
        
        # 最大回転角度の検出
        valid_shoulder_rotations = [angle for angle in shoulder_rotations if angle is not None]
        valid_hip_rotations = [angle for angle in hip_rotations if angle is not None]
        
        max_shoulder_rotation = max(valid_shoulder_rotations) if valid_shoulder_rotations else 0
        max_hip_rotation = max(valid_hip_rotations) if valid_hip_rotations else 0
        
        # 評価（厳格化された基準）
        shoulder_score = 10.0
        hip_score = 10.0
        issues = []
        
        # 肩の回転評価（理想: 88-92度）
        if max_shoulder_rotation < 75:
            issues.append("肩の回転が大幅に不足しています")
            shoulder_score -= 6.0
        elif max_shoulder_rotation < 83:
            issues.append("肩の回転が不足しています")
            shoulder_score -= 4.0
        elif max_shoulder_rotation < 88:
            issues.append("肩の回転がやや不足しています")
            shoulder_score -= 2.0
        elif max_shoulder_rotation > 98:
            issues.append("肩の回転が過度です")
            shoulder_score -= 5.0
        elif max_shoulder_rotation > 92:
            issues.append("肩の回転がやや過度です")
            shoulder_score -= 2.5
        
        # 腰の回転評価（理想: 45-55度）
        if max_hip_rotation < 30:
            issues.append("腰の回転が大幅に不足しています")
            hip_score -= 6.0
        elif max_hip_rotation < 40:
            issues.append("腰の回転が不足しています")
            hip_score -= 4.0
        elif max_hip_rotation < 45:
            issues.append("腰の回転がやや不足しています")
            hip_score -= 2.0
        elif max_hip_rotation > 65:
            issues.append("腰の回転が過度です")
            hip_score -= 5.0
        elif max_hip_rotation > 55:
            issues.append("腰の回転がやや過度です")
            hip_score -= 2.5
        
        overall_rotation_score = (shoulder_score + hip_score) / 2
        
        return {
            'max_shoulder_rotation': max_shoulder_rotation,
            'max_hip_rotation': max_hip_rotation,
            'shoulder_score': shoulder_score,
            'hip_score': hip_score,
            'overall_score': overall_rotation_score,
            'issues': issues,
            'recommendations': self._get_rotation_recommendations(max_shoulder_rotation, max_hip_rotation, issues)
        }
    
    def analyze_timing(self, pose_results: List[Dict], serve_phases: List[ServePhase]) -> Dict:
        """
        タイミングの解析
        
        Args:
            pose_results: ポーズ検出結果リスト
            serve_phases: サーブフェーズリスト
            
        Returns:
            タイミング解析結果
        """
        total_duration = len(pose_results) / 30.0  # 30fps想定
        
        # 各フェーズの理想的な時間配分（全体に対する割合）
        ideal_phase_ratios = {
            'preparation': 0.15,
            'ball_toss': 0.20,
            'trophy_position': 0.25,
            'acceleration': 0.15,
            'contact': 0.05,
            'follow_through': 0.20
        }
        
        timing_scores = {}
        timing_issues = []
        
        for phase in serve_phases:
            phase_duration = phase.duration
            phase_ratio = phase_duration / total_duration if total_duration > 0 else 0
            ideal_ratio = ideal_phase_ratios.get(phase.name, 0.15)
            
            # 理想との差を評価（厳格化された基準）
            ratio_diff = abs(phase_ratio - ideal_ratio)
            
            if ratio_diff < 0.03:  # 3%以内
                phase_score = 10.0
            elif ratio_diff < 0.06:  # 6%以内
                phase_score = 8.5
            elif ratio_diff < 0.1:   # 10%以内
                phase_score = 7.0
            elif ratio_diff < 0.15:  # 15%以内
                phase_score = 5.5
            elif ratio_diff < 0.2:   # 20%以内
                phase_score = 4.0
            else:
                phase_score = 2.0
                if phase_ratio > ideal_ratio:
                    timing_issues.append(f"{phase.name}フェーズが長すぎます")
                else:
                    timing_issues.append(f"{phase.name}フェーズが短すぎます")
            
            timing_scores[phase.name] = phase_score
        
        overall_timing_score = np.mean(list(timing_scores.values())) if timing_scores else 0.0
        
        return {
            'total_duration': total_duration,
            'phase_scores': timing_scores,
            'overall_score': overall_timing_score,
            'issues': timing_issues,
            'recommendations': self._get_timing_recommendations(timing_issues)
        }
    
    def calculate_overall_score(self, analysis_results: Dict) -> float:
        """
        総合スコアの計算
        
        Args:
            analysis_results: 各技術要素の解析結果
            
        Returns:
            総合スコア（0-10）
        """
        scores = []
        weights = {
            'knee_movement': 0.05,      # 膝の動き（基礎）- さらに削減
            'elbow_position': 0.20,     # 肘の位置（重要）- 増加
            'toss_trajectory': 0.15,    # トス軌道（重要）- 維持
            'body_rotation': 0.30,      # 体回転（最重要）- 大幅増加
            'timing': 0.05,             # タイミング（基礎）- さらに削減
            'follow_through': 0.25      # フォロースルー（最重要）- 維持
        }
        
        for category, weight in weights.items():
            if category in analysis_results:
                category_score = analysis_results[category].get('overall_score', 0.0)
                scores.append(category_score * weight)
        
        return sum(scores) if scores else 0.0
    
    # ヘルパーメソッド
    def _extract_landmark_trajectory(self, pose_results: List[Dict], landmark_name: str) -> List[Optional[Dict]]:
        """ランドマークの軌道を抽出"""
        trajectory = []
        print(f"=== {landmark_name}軌道抽出開始 ===")
        print(f"入力フレーム数: {len(pose_results)}")
        
        valid_count = 0
        for i, result in enumerate(pose_results):
            if result['has_pose'] and landmark_name in result.get('landmarks', {}):
                trajectory.append(result['landmarks'][landmark_name])
                valid_count += 1
                if i < 5:  # 最初の5フレームをログ出力
                    print(f"フレーム {i}: {landmark_name} = {result['landmarks'][landmark_name]}")
            else:
                trajectory.append(None)
                if i < 5:  # 最初の5フレームをログ出力
                    has_pose = result.get('has_pose', False)
                    has_landmark = landmark_name in result.get('landmarks', {})
                    print(f"フレーム {i}: has_pose={has_pose}, has_{landmark_name}={has_landmark}")
        
        print(f"{landmark_name}軌道: 有効データ {valid_count}/{len(pose_results)} フレーム")
        return trajectory
    
    def _calculate_joint_angle(self, point1: Optional[Dict], point2: Optional[Dict], point3: Optional[Dict]) -> Optional[float]:
        """3点から関節角度を計算"""
        if not all([point1, point2, point3]):
            return None
        
        # デバッグ: 入力座標を確認
        # print(f"角度計算: p1=({point1['x']:.3f},{point1['y']:.3f}), p2=({point2['x']:.3f},{point2['y']:.3f}), p3=({point3['x']:.3f},{point3['y']:.3f})")
        
        # ベクトル計算
        v1 = np.array([point1['x'] - point2['x'], point1['y'] - point2['y']])
        v2 = np.array([point3['x'] - point2['x'], point3['y'] - point2['y']])
        
        # ベクトルの長さチェック
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 < 1e-6 or norm2 < 1e-6:
            # print(f"⚠️ ベクトル長が極小: norm1={norm1:.6f}, norm2={norm2:.6f}")
            return None
        
        # 角度計算
        cos_angle = np.dot(v1, v2) / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        # デバッグ: 計算結果を確認
        # print(f"計算結果: cos_angle={cos_angle:.3f}, angle={angle:.1f}度")
        
        return angle
    
    def _calculate_rotation_angle(self, left_point: Dict, right_point: Dict) -> float:
        """2点から回転角度を計算"""
        dx = right_point['x'] - left_point['x']
        dy = right_point['y'] - left_point['y']
        angle = math.atan2(dy, dx) * 180 / math.pi
        return abs(angle)
    
    def _calculate_trajectory_smoothness(self, trajectory: List[Dict]) -> float:
        """軌道の滑らかさを計算（Noneチェック追加）"""
        if len(trajectory) < 3:
            return 0.0
        
        # Noneでない有効なポイントのみを抽出
        valid_points = [point for point in trajectory if point is not None]
        
        if len(valid_points) < 3:
            return 0.0
        
        # 速度変化の標準偏差を計算
        velocities = []
        for i in range(1, len(valid_points)):
            dx = valid_points[i]['x'] - valid_points[i-1]['x']
            dy = valid_points[i]['y'] - valid_points[i-1]['y']
            velocity = math.sqrt(dx*dx + dy*dy)
            velocities.append(velocity)
        
        if len(velocities) < 2:
            return 1.0
        
        velocity_std = np.std(velocities)
        velocity_mean = np.mean(velocities)
        
        # 正規化された滑らかさスコア
        if velocity_mean == 0:
            return 1.0
        
        smoothness = 1.0 - min(velocity_std / velocity_mean, 1.0)
        return max(smoothness, 0.0)
    
    def _extract_video_metadata(self, pose_results: List[Dict]) -> Dict:
        """動画メタデータの抽出"""
        if not pose_results:
            return {
                'total_frames': 0,
                'duration': 0.0,
                'fps': 0.0,
                'detected_frames': 0
            }
        
        total_frames = len(pose_results)
        detected_frames = sum(1 for result in pose_results if result.get('has_pose', False))
        
        # フレームレートの推定（タイムスタンプから）
        fps = 30.0  # デフォルト値
        if len(pose_results) > 1:
            first_timestamp = pose_results[0].get('timestamp', 0.0)
            last_timestamp = pose_results[-1].get('timestamp', 0.0)
            if last_timestamp > first_timestamp:
                duration = last_timestamp - first_timestamp
                fps = (total_frames - 1) / duration if duration > 0 else 30.0
            else:
                duration = total_frames / fps
        else:
            duration = total_frames / fps
        
        return {
            'total_frames': total_frames,
            'duration': duration,
            'fps': fps,
            'detected_frames': detected_frames,
            'detection_rate': detected_frames / total_frames if total_frames > 0 else 0.0
        }
    
    def _create_fallback_phases(self, total_frames: int) -> List[ServePhase]:
        """フォールバック用の均等分割フェーズ"""
        phase_lengths = [0.15, 0.20, 0.25, 0.15, 0.05, 0.20]  # 各フェーズの割合
        phases = []
        current_frame = 0
        
        for i, (phase_name, ratio) in enumerate(zip(self.serve_phases, phase_lengths)):
            phase_length = int(total_frames * ratio)
            if i == len(self.serve_phases) - 1:  # 最後のフェーズ
                phase_length = total_frames - current_frame
            
            phases.append(ServePhase(
                name=phase_name,
                start_frame=current_frame,
                end_frame=current_frame + phase_length - 1,
                duration=phase_length / 30.0,
                key_events=[]
            ))
            current_frame += phase_length
        
        return phases
    
    def _generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """総合的な推奨事項の生成"""
        recommendations = []
        
        for category, results in analysis_results.items():
            if 'recommendations' in results:
                recommendations.extend(results['recommendations'])
        
        return recommendations
    
    def _get_knee_recommendations(self, max_bend_angle: float, timing_issues: List[str], depth_issues: List[str]) -> List[str]:
        """膝の動きに関する推奨事項"""
        recommendations = []
        
        if max_bend_angle > 160:
            recommendations.append("膝をもっと深く曲げて、より多くのパワーを生成しましょう")
        elif max_bend_angle < 120:
            recommendations.append("膝の曲げを少し浅くして、バランスを保ちましょう")
        
        if "膝の曲げが早すぎます" in timing_issues:
            recommendations.append("トスと同時に膝を曲げ始めるタイミングを練習しましょう")
        elif "膝の曲げが遅すぎます" in timing_issues:
            recommendations.append("もう少し早めに膝を曲げ始めましょう")
        
        return recommendations
    
    def _get_elbow_recommendations(self, elbow_shoulder_diff: float, issues: List[str]) -> List[str]:
        """肘の位置に関する推奨事項"""
        recommendations = []
        
        if elbow_shoulder_diff < -0.05:
            recommendations.append("肘をもう少し高い位置に保ちましょう")
        elif elbow_shoulder_diff > 0.1:
            recommendations.append("肘の位置を少し下げて、自然な動作を心がけましょう")
        
        if "肘の動きが不安定です" in issues:
            recommendations.append("肘の軌道を安定させるため、ゆっくりとした練習から始めましょう")
        
        return recommendations
    
    def _get_toss_recommendations(self, max_height: float, forward_distance: float, issues: List[str]) -> List[str]:
        """トスに関する推奨事項"""
        recommendations = []
        
        if max_height < 0.3:
            recommendations.append("トスをもう少し高く上げて、十分な時間を確保しましょう")
        elif max_height > 0.7:
            recommendations.append("トスの高さを少し抑えて、コントロールを向上させましょう")
        
        if forward_distance < 0.05:
            recommendations.append("トスをもう少し前方に投げて、効果的な打点を作りましょう")
        elif forward_distance > 0.2:
            recommendations.append("トスの前方距離を抑えて、バランスを保ちましょう")
        
        return recommendations
    
    def _get_rotation_recommendations(self, shoulder_rotation: float, hip_rotation: float, issues: List[str]) -> List[str]:
        """体の回転に関する推奨事項"""
        recommendations = []
        
        if shoulder_rotation < 60:
            recommendations.append("肩の回転をもっと大きくして、パワーを増加させましょう")
        elif shoulder_rotation > 120:
            recommendations.append("肩の回転を少し抑えて、コントロールを向上させましょう")
        
        if hip_rotation < 30:
            recommendations.append("腰の回転を意識して、下半身からのパワー伝達を改善しましょう")
        
        return recommendations
    
    def _get_timing_recommendations(self, timing_issues: List[str]) -> List[str]:
        """タイミングに関する推奨事項"""
        recommendations = []
        
        if timing_issues:
            recommendations.append("各フェーズのタイミングを意識して、リズムの良いサーブを心がけましょう")
            recommendations.append("メトロノームを使った練習で、一定のリズムを身につけましょう")
        
        return recommendations


def main():
    """テスト用のメイン関数"""
    # テスト用のダミーデータ
    dummy_pose_results = [
        {
            'frame_number': i,
            'timestamp': i / 30.0,
            'has_pose': True,
            'landmarks': {
                'right_wrist': {'x': 0.5 + i * 0.01, 'y': 0.5 - i * 0.005, 'z': 0.0, 'visibility': 0.9},
                'left_wrist': {'x': 0.4 - i * 0.005, 'y': 0.6 - i * 0.01, 'z': 0.0, 'visibility': 0.9},
                'right_elbow': {'x': 0.45 + i * 0.008, 'y': 0.4 - i * 0.003, 'z': 0.0, 'visibility': 0.8},
                'right_shoulder': {'x': 0.5, 'y': 0.3, 'z': 0.0, 'visibility': 0.9},
                'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9},
                'right_knee': {'x': 0.52, 'y': 0.8, 'z': 0.0, 'visibility': 0.8},
                'right_hip': {'x': 0.5, 'y': 0.6, 'z': 0.0, 'visibility': 0.9},
                'right_ankle': {'x': 0.53, 'y': 1.0, 'z': 0.0, 'visibility': 0.7}
            }
        } for i in range(150)  # 5秒間のダミーデータ
    ]
    
    analyzer = MotionAnalyzer()
    
    try:
        # 動作解析実行
        analysis_result = analyzer.analyze_serve_motion(dummy_pose_results)
        
        # 結果表示
        print("=== テニスサービス動作解析結果 ===")
        print(f"総合スコア: {analysis_result['overall_score']:.1f}/10.0")
        print(f"動画時間: {analysis_result['video_metadata']['duration']:.1f}秒")
        
        print("\n=== 技術要素別スコア ===")
        for category, results in analysis_result['technical_analysis'].items():
            print(f"{category}: {results['overall_score']:.1f}/10.0")
            if results.get('issues'):
                for issue in results['issues']:
                    print(f"  - {issue}")
        
        print("\n=== 推奨事項 ===")
        for recommendation in analysis_result['recommendations']:
            print(f"- {recommendation}")
        
        # 結果をJSONファイルに保存
        with open('analysis_result.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print("\n解析結果をanalysis_result.jsonに保存しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()

