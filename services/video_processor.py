import cv2
import numpy as np
import os
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import time
import subprocess

class VideoProcessor:
    def __init__(self, max_file_size: int = 100 * 1024 * 1024):
        self.supported_formats = ['.mov', '.mp4', '.avi', '.mkv', '.wmv']
        self.max_file_size = max_file_size
        self.temp_dir = tempfile.mkdtemp(prefix='tennis_analyzer_')
        self.max_duration = 30
        self.target_fps = 20
        self.target_resolution = (960, 540)

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def validate_video(self, file_path: str) -> Dict[str, Union[bool, str, Dict]]:
        validation_result = {
            'is_valid': False,
            'error_message': '',
            'warnings': [],
            'metadata': {}
        }
        try:
            if not os.path.exists(file_path):
                validation_result['error_message'] = 'ファイルが存在しません'
                return validation_result
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                validation_result['error_message'] = f'ファイルサイズが大きすぎます（最大: {self.max_file_size // (1024*1024)}MB）'
                return validation_result
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in self.supported_formats:
                validation_result['error_message'] = f'サポートされていないファイル形式です（対応形式: {", ".join(self.supported_formats)}）'
                return validation_result
            metadata = self.get_video_metadata(file_path)
            if not metadata:
                validation_result['error_message'] = '動画ファイルを読み込めません'
                return validation_result
            validation_result['metadata'] = metadata
            if metadata['duration'] > self.max_duration:
                validation_result['warnings'].append(f'動画が長すぎます（推奨: {self.max_duration}秒以下）')
            if metadata['width'] < 640 or metadata['height'] < 480:
                validation_result['warnings'].append('解像度が低すぎる可能性があります（推奨: 640x480以上）')
            if metadata['fps'] < 15:
                validation_result['warnings'].append('フレームレートが低すぎる可能性があります（推奨: 15fps以上）')
            if metadata['frame_count'] < 30:
                validation_result['warnings'].append('動画が短すぎる可能性があります（推奨: 1秒以上）')
            validation_result['is_valid'] = True
            return validation_result
        except Exception as e:
            validation_result['error_message'] = f'検証中にエラーが発生しました: {str(e)}'
            return validation_result

    def get_video_metadata(self, file_path: str) -> Optional[Dict]:
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return None
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()

            # ffprobeでrotation取得
            rotate = 0
            try:
                cmd = [
                    'ffprobe', '-v', 'error', '-show_streams',
                    file_path
                ]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
                for line in output.splitlines():
                    line = line.strip().lower()
                    if line.startswith("rotation="):
                        val = line.replace("rotation=", "").strip()
                        try:
                            rotate = int(val)
                            break
                        except Exception:
                            continue
            except Exception as e:
                print("ffprobe rotation解析失敗:", e)
                rotate = 0

            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'file_size': os.path.getsize(file_path),
                'format': Path(file_path).suffix.lower(),
                'rotate': rotate
            }
        except Exception as e:
            print(f"メタデータ取得エラー: {e}")
            return None

    def extract_frames(self, video_path: str, max_frames: int = 200) -> List[np.ndarray]:
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"動画ファイルを開けません: {video_path}")
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = 1 if total_frames <= max_frames else total_frames // max_frames
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_index % frame_interval == 0:
                    frames.append(frame)
                    if len(frames) >= max_frames:
                        break
                frame_index += 1
            cap.release()
        except Exception as e:
            print(f"フレーム抽出エラー: {e}")
            return []
        return frames

    def preprocess_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f"preprocessed_{int(time.time())}.mp4")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"動画ファイルを開けません: {video_path}")

        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)

        output_width, output_height = self._calculate_output_resolution(original_width, original_height)
        output_fps = min(original_fps, self.target_fps)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (output_width, output_height))
        try:
            frame_count = 0
            max_frames = int(output_fps * self.max_duration)
            while True:
                ret, frame = cap.read()
                if not ret or frame_count >= max_frames:
                    break
                if (original_width, original_height) != (output_width, output_height):
                    frame = cv2.resize(frame, (output_width, output_height))
                out.write(frame)
                frame_count += 1
        finally:
            cap.release()
            out.release()
        return output_path

    def rotate_video_if_needed(self, input_path: str, output_path: str, rotate: int) -> str:
        print(f"入力rotate値: {rotate}")
        if rotate == 0:
            print("回転不要")
            return input_path

        if rotate == -90:
            transpose_val = 3  # 反時計回り
        elif rotate == 90:
            transpose_val = 1  # 時計回り
        elif rotate == 180 or rotate == -180:
            transpose_val = 2
        elif rotate == -270:
            transpose_val = 1
        elif rotate == 270:
            transpose_val = 3
        else:
            raise ValueError(f"未対応の回転角度: {rotate}")

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"transpose={transpose_val}",
            "-metadata:s:v", "rotate=0",
            output_path
        ]
        print("実行ffmpegコマンド:", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("ffmpeg回転OK:", output_path)
        except subprocess.CalledProcessError as e:
            print("ffmpeg回転エラー:", e.stderr.decode())
            raise

        return output_path

    def _calculate_output_resolution(self, width: int, height: int) -> Tuple[int, int]:
        target_width, target_height = self.target_resolution
        aspect_ratio = width / height
        target_aspect_ratio = target_width / target_height
        if aspect_ratio > target_aspect_ratio:
            output_width = target_width
            output_height = int(target_width / aspect_ratio)
        else:
            output_height = target_height
            output_width = int(target_height * aspect_ratio)
        output_width = output_width - (output_width % 2)
        output_height = output_height - (output_height % 2)
        return output_width, output_height
