"""
オーバーレイ画像生成サービス
テニスサーブ解析システム用
"""
import os
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional, Tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverlayImageGenerator:
    """オーバーレイ画像生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
    def generate_overlay_images(self, video_path: str, pose_results: List[Dict], output_dir: str) -> Dict[str, Any]:
        """
        動画からオーバーレイ画像を生成
        
        Args:
            video_path: 動画ファイルパス
            pose_results: ポーズ検出結果
            output_dir: 出力ディレクトリ
            
        Returns:
            生成結果の辞書
        """
        try:
            self.logger.info("🎨 オーバーレイ画像生成を開始")
            
            # 出力ディレクトリ作成
            overlay_dir = os.path.join(output_dir, 'overlay_images')
            os.makedirs(overlay_dir, exist_ok=True)
            
            # 利き手判定
            dominant_hand = self._detect_dominant_hand(pose_results)
            self.logger.info(f"🟢 利き手判定: {dominant_hand}")
            
            # トロフィーポーズ検出
            trophy_frame = self._detect_trophy_pose(pose_results, dominant_hand)
            
            # 代表フレーム選択
            frame_indices = self._select_representative_frames(pose_results, trophy_frame)
            self.logger.info(f"🎯 選択フレーム: {frame_indices}")
            
            # オーバーレイ画像生成
            saved_images = self._generate_images(video_path, pose_results, frame_indices, overlay_dir)
            
            result = {
                'success': True,
                'dominant_hand': dominant_hand,
                'trophy_frame': trophy_frame,
                'frame_indices': frame_indices,
                'saved_images': saved_images,
                'image_count': len(saved_images),
                'output_directory': overlay_dir
            }
            
            self.logger.info(f"🎉 オーバーレイ画像生成完了: {len(saved_images)}枚")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ オーバーレイ画像生成エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'saved_images': [],
                'image_count': 0
            }
    
    def _detect_dominant_hand(self, pose_results: List[Dict]) -> str:
        """利き手を自動判定"""
        right_hand_raised = 0
        left_hand_raised = 0
        
        for result in pose_results:
            if result.get("has_pose") and result.get("landmarks"):
                landmarks = result["landmarks"]
                
                # 右手の判定
                rw = landmarks.get("right_wrist", {})
                rs = landmarks.get("right_shoulder", {})
                if rw and rs and rw.get("y", float('inf')) < rs.get("y", 0):
                    right_hand_raised += 1
                
                # 左手の判定
                lw = landmarks.get("left_wrist", {})
                ls = landmarks.get("left_shoulder", {})
                if lw and ls and lw.get("y", float('inf')) < ls.get("y", 0):
                    left_hand_raised += 1
        
        return "right" if right_hand_raised >= left_hand_raised else "left"
    
    def _detect_trophy_pose(self, pose_results: List[Dict], dominant_hand: str) -> Optional[int]:
        """トロフィーポーズを検出"""
        candidate_frames = []
        
        for result in pose_results:
            if result.get("has_pose") and result.get("landmarks"):
                landmarks = result["landmarks"]
                frame_number = result.get("frame_number", 0)
                
                # 利き手のランドマーク取得
                wrist = landmarks.get(f"{dominant_hand}_wrist", {})
                elbow = landmarks.get(f"{dominant_hand}_elbow", {})
                shoulder = landmarks.get(f"{dominant_hand}_shoulder", {})
                
                if all([wrist, elbow, shoulder]):
                    # トロフィーポーズの特徴: 肘・手首が肩より高い
                    if (elbow.get("y", float('inf')) < shoulder.get("y", 0) and 
                        wrist.get("y", float('inf')) < shoulder.get("y", 0)):
                        candidate_frames.append((frame_number, wrist.get("y", 0)))
        
        if candidate_frames:
            # 手首が最も高いフレームをトロフィーポーズとする
            candidate_frames.sort(key=lambda x: x[1])
            trophy_frame = candidate_frames[0][0]
            self.logger.info(f"🏆 トロフィーポーズ検出: フレーム {trophy_frame}")
            return trophy_frame
        else:
            self.logger.warning("⚠️ トロフィーポーズ検出失敗")
            return None
    
    def _select_representative_frames(self, pose_results: List[Dict], trophy_frame: Optional[int]) -> List[int]:
        """代表フレームを選択"""
        total_frames = len(pose_results)
        
        if trophy_frame is not None:
            # トロフィーポーズ前後30フレームで等間隔5枚
            window = 30
            start_frame = max(trophy_frame - window, 0)
            end_frame = min(trophy_frame + window, total_frames - 1)
            frame_indices = np.linspace(start_frame, end_frame, num=5, dtype=int).tolist()
        else:
            # 保険として全体から均等5枚
            frame_indices = np.linspace(0, total_frames - 1, num=5, dtype=int).tolist()
        
        return frame_indices
    
    def _generate_images(self, video_path: str, pose_results: List[Dict], 
                        frame_indices: List[int], output_dir: str) -> List[Dict]:
        """オーバーレイ画像を生成"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"動画を開けません: {video_path}")
        
        saved_images = []
        
        try:
            for idx, frame_no in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ret, frame = cap.read()
                if not ret:
                    self.logger.warning(f"❌ フレーム読み込み失敗: フレーム番号 {frame_no}")
                    continue
                
                # オーバーレイ描画
                pose_data = pose_results[frame_no] if frame_no < len(pose_results) else {}
                annotated_frame = self._draw_pose_landmarks(frame, pose_data)
                
                # 画像保存
                filename = f"pose_{idx:03d}.jpg"
                save_path = os.path.join(output_dir, filename)
                success = cv2.imwrite(save_path, annotated_frame)
                
                if success:
                    self.logger.info(f"✅ 保存成功: {filename}")
                    saved_images.append({
                        'filename': filename,
                        'path': save_path,
                        'frame_number': frame_no,
                        'index': idx
                    })
                else:
                    self.logger.error(f"❌ 保存失敗: {filename}")
        
        finally:
            cap.release()
        
        return saved_images
    
    def _draw_pose_landmarks(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """ポーズランドマークを描画"""
        if not pose_data.get("has_pose") or not pose_data.get("landmarks"):
            return frame
        
        landmarks = pose_data["landmarks"]
        annotated_frame = frame.copy()
        
        # 接続線の定義
        connections = [
            # 胴体
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
            
            # 左腕
            ("left_shoulder", "left_elbow"),
            ("left_elbow", "left_wrist"),
            
            # 右腕
            ("right_shoulder", "right_elbow"),
            ("right_elbow", "right_wrist"),
            
            # 左脚
            ("left_hip", "left_knee"),
            ("left_knee", "left_ankle"),
            
            # 右脚
            ("right_hip", "right_knee"),
            ("right_knee", "right_ankle"),
        ]
        
        # 接続線を描画
        for start_point, end_point in connections:
            start_landmark = landmarks.get(start_point)
            end_landmark = landmarks.get(end_point)
            
            if start_landmark and end_landmark:
                start_pos = (int(start_landmark["x"]), int(start_landmark["y"]))
                end_pos = (int(end_landmark["x"]), int(end_landmark["y"]))
                cv2.line(annotated_frame, start_pos, end_pos, (0, 255, 0), 2)
        
        # ランドマークポイントを描画
        for landmark_name, landmark in landmarks.items():
            if landmark:
                pos = (int(landmark["x"]), int(landmark["y"]))
                cv2.circle(annotated_frame, pos, 5, (0, 0, 255), -1)
        
        return annotated_frame

