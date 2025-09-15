"""
テニスサービス動作解析 - ポーズ検出サービス（高速化版）
MediaPipeを使用した人体ポーズ検出機能
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import time
import os

class PoseDetector:
    """MediaPipeを使用したポーズ検出クラス"""

    def __init__(self, 
                 model_complexity: int = 1,  # 最軽量化（元々は1）
                 min_detection_confidence: float = 0.4,
                 min_tracking_confidence: float = 0.4):
        """
        ポーズ検出器の初期化
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        # テニスサービス解析に重要なランドマーク
        self.key_landmarks = {
            'nose': 0,
            'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8,
            'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20,
            'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }

    def detect_poses(self, video_path: str, output_dir: str, skip_frames: int = 6, resize_dim=(640, 360)) -> List[Dict]:
        """
        動画からポーズを検出（main.pyから呼び出されるメインメソッド）

        Args:
            video_path: 入力動画ファイルパス
            output_dir: 出力ディレクトリ
            skip_frames: フレーム間引き値（例:8なら8フレームに1回だけ検出。元々は6）
            resize_dim: リサイズ先解像度（幅,高さ）のタプル

        Returns:
            全フレームのポーズ検出結果リスト
        """
        try:
            print(f"ポーズ検出開始: {video_path}")
            start_time = time.time()
            output_json_path = os.path.join(output_dir, f"pose_data_{int(time.time())}.json")

            pose_results = self.process_video(video_path, skip_frames, resize_dim)
            self.save_pose_data(pose_results, output_json_path)

            elapsed = time.time() - start_time
            print(f"ポーズ検出完了: {len(pose_results)}フレーム ({elapsed:.1f}秒)")

            return pose_results
        except Exception as e:
            print(f"ポーズ検出エラー: {e}")
            return []

    def detect_pose(self, frame: np.ndarray, frame_number: int = 0, timestamp: float = 0.0) -> Dict:
        """
        単一フレームのポーズ検出
        """
        # BGR→RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # ここでリサイズ（640x360など）
        small_frame = cv2.resize(rgb_frame, (640, 360))

        results = self.pose.process(small_frame)

        pose_data = {
            'frame_number': frame_number,
            'timestamp': timestamp,
            'landmarks': {},
            'visibility_scores': {},
            'detection_confidence': 0.0,
            'has_pose': False
        }

        if results.pose_landmarks:
            pose_data['has_pose'] = True

            # 画像サイズ変わっても、相対座標(x,y:0-1)なのでOK
            for landmark_name, landmark_idx in self.key_landmarks.items():
                if landmark_idx < len(results.pose_landmarks.landmark):
                    landmark = results.pose_landmarks.landmark[landmark_idx]
                    pose_data['landmarks'][landmark_name] = {
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    }
                    pose_data['visibility_scores'][landmark_name] = landmark.visibility

            if pose_data['visibility_scores']:
                pose_data['detection_confidence'] = np.mean(list(pose_data['visibility_scores'].values()))

        return pose_data

    def process_video(self, video_path: str, skip_frames: int = 6, resize_dim=(640, 360)) -> List[Dict]:
        """
        動画全体のポーズ検出処理
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"動画ファイルを開けません: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        pose_results = []
        frame_number = 0
        processed_frames = 0

        print(f"動画情報: {fps:.1f}fps, {frame_count}フレーム")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % skip_frames == 0:
                timestamp = frame_number / fps
                try:
                    pose_data = self.detect_pose(frame, frame_number, timestamp)
                except Exception as e:
                    print(f"フレーム {frame_number}: detect_poseでエラー - {e}")
                    pose_data = {
                        'frame_number': frame_number,
                        'timestamp': timestamp,
                        'landmarks': {},
                        'visibility_scores': {},
                        'detection_confidence': 0.0,
                        'has_pose': False
                    }
                pose_results.append(pose_data)
                processed_frames += 1

                # 進捗表示
                if processed_frames % 10 == 0:
                    progress = (frame_number / frame_count) * 100
                    print(f"進捗: {progress:.1f}% ({processed_frames}枚処理)")

            frame_number += 1

        cap.release()

        print(f"総フレーム数: {frame_count} / 解析フレーム数: {processed_frames}")
        return pose_results

    def _draw_pose_landmarks(self, frame: np.ndarray, pose_data: Dict) -> np.ndarray:
        """
        フレームにポーズランドマークを描画
        """
        annotated_frame = frame.copy()
        if not pose_data['has_pose']:
            return annotated_frame

        landmarks = pose_data['landmarks']
        height, width = frame.shape[:2]

        key_points = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
                     'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 
                     'left_knee', 'right_knee', 'left_ankle', 'right_ankle']

        for point_name in key_points:
            if point_name in landmarks:
                landmark = landmarks[point_name]
                x = int(landmark['x'] * width)
                y = int(landmark['y'] * height)
                visibility = pose_data['visibility_scores'].get(point_name, 0)
                if visibility > 0.5:
                    color = (0, 255, 0)
                elif visibility > 0.3:
                    color = (0, 255, 255)
                else:
                    color = (0, 0, 255)
                cv2.circle(annotated_frame, (x, y), 5, color, -1)

        connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle')
        ]

        for start_point, end_point in connections:
            if start_point in landmarks and end_point in landmarks:
                start_landmark = landmarks[start_point]
                end_landmark = landmarks[end_point]
                start_x = int(start_landmark['x'] * width)
                start_y = int(start_landmark['y'] * height)
                end_x = int(end_landmark['x'] * width)
                end_y = int(end_landmark['y'] * height)
                cv2.line(annotated_frame, (start_x, start_y), (end_x, end_y), (255, 255, 255), 2)

        confidence = pose_data['detection_confidence']
        cv2.putText(annotated_frame, f'Confidence: {confidence:.2f}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        return annotated_frame

    def save_pose_data(self, pose_results: List[Dict], output_path: str):
        """
        ポーズ検出結果をJSONファイルに保存
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pose_results, f, indent=2, ensure_ascii=False)
        print(f"ポーズデータ保存完了: {output_path}")

    def load_pose_data(self, input_path: str) -> List[Dict]:
        with open(input_path, 'r', encoding='utf-8') as f:
            pose_results = json.load(f)
        print(f"ポーズデータ読み込み完了: {len(pose_results)}フレーム")
        return pose_results

    def get_pose_statistics(self, pose_results: List[Dict]) -> Dict:
        if not pose_results:
            return {}
        total_frames = len(pose_results)
        detected_frames = sum(1 for p in pose_results if p['has_pose'])
        detection_rate = (detected_frames / total_frames) * 100
        confidences = [p['detection_confidence'] for p in pose_results if p['has_pose']]
        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = np.max(confidences) if confidences else 0
        min_confidence = np.min(confidences) if confidences else 0
        landmark_detection_rates = {}
        for landmark_name in self.key_landmarks.keys():
            detected_count = sum(1 for p in pose_results if p['has_pose'] and landmark_name in p['landmarks'])
            landmark_detection_rates[landmark_name] = (detected_count / detected_frames) * 100 if detected_frames > 0 else 0
        return {
            'total_frames': total_frames,
            'detected_frames': detected_frames,
            'detection_rate': detection_rate,
            'confidence_stats': {
                'average': avg_confidence,
                'maximum': max_confidence,
                'minimum': min_confidence
            },
            'landmark_detection_rates': landmark_detection_rates,
            'duration': pose_results[-1]['timestamp'] if pose_results else 0
        }

    def __del__(self):
        if hasattr(self, 'pose') and self.pose:
            self.pose.close()

def main():
    detector = PoseDetector()
    test_video = "test_video.mp4"
    output_dir = "output"
    if os.path.exists(test_video):
        os.makedirs(output_dir, exist_ok=True)
        # 高速化指定！skip_frames=6, resize_dim=(640,360)
        pose_results = detector.detect_poses(test_video, output_dir, skip_frames=6, resize_dim=(640,360))
        stats = detector.get_pose_statistics(pose_results)
        print("統計情報:", json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(f"テスト動画が見つかりません: {test_video}")

if __name__ == "__main__":
    main()
