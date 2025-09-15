"""
テニスサーブ解析システム - メインアプリケーション（有料・無料プラン完全分離/セキュアAPI運用版）
"""

import os
import argparse
import logging
import traceback
import subprocess
import json
import time, shutil 
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv
load_dotenv()

# サービスのインポート
from utils import generate_overlay_images_with_dominant_hand
from services.video_processor import VideoProcessor
from services.pose_detector import PoseDetector
from services.motion_analyzer import MotionAnalyzer
from services.advice_generator import AdviceGenerator
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    static_url_path='/static'
)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/output'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_rotation_ffprobe(file_path):
    """ffprobeで回転情報取得"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-print_format', 'json',
            '-show_streams', '-show_format', file_path
        ]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        meta = json.loads(output)
        rotate = 0
        for stream in meta.get('streams', []):
            tags = stream.get('tags', {})
            if 'rotate' in tags:
                try:
                    rotate = int(tags['rotate'])
                    break
                except Exception:
                    pass
            for side_data in stream.get('side_data_list', []):
                if 'rotation' in side_data:
                    try:
                        rotate = int(side_data['rotation'])
                        break
                    except Exception:
                        pass
        return rotate
    except Exception as e:
        logger.warning(f"ffprobe回転取得エラー: {e}")
        return 0

def ffmpeg_one_shot(input_path, output_path, rotate, target_res=(960, 540), target_fps=20):
    """ffmpeg一発で回転/リサイズ/リフレッシュ"""
    vf = []
    if rotate == 90:
        vf.append("transpose=1")
    elif rotate == -90 or rotate == 270:
        vf.append("transpose=2")
    elif rotate == 180 or rotate == -180:
        vf.append("hflip,vflip")
    vf.append(f"scale={target_res[0]}:{target_res[1]}")
    vf.append(f"fps={target_fps}")
    vf_filter = ",".join(vf)
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf_filter,
        "-preset", "ultrafast",
        "-threads", "4",
        "-metadata:s:v", "rotate=0",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"ffmpeg一発変換完了: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg一発変換失敗: {e.stderr.decode()}")
        return input_path

@app.route('/')
def index():
    return app.send_static_file("index.html")

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    print('[HIT] /api/analyze', request.headers.get('Content-Length'))
    print('[FORM]', request.form.to_dict())
    f = request.files.get('video')
    print(' file=', f.filename if f else None)
    try:
        logger.info("=== 動画解析リクエスト受信 ===")
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'ビデオファイルが見つかりません'}), 400

        file = request.files['video']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'ファイルが選択されていません'}), 400
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '対応していないファイル形式です'}), 400

        # ファイル保存
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        video_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(video_path)
        logger.info(f"ファイル保存完了: {video_path}")

        # (1) 回転取得
        rotate = detect_rotation_ffprobe(video_path)
        logger.info(f"ffprobe回転角度: {rotate}")

        # (2) ffmpeg一発変換
        processed_name = f"processed_{unique_filename}"
        processed_path = os.path.join(UPLOAD_FOLDER, processed_name)
        processed_path = ffmpeg_one_shot(video_path, processed_path, rotate)

        # (3) 解析用出力ディレクトリ
        out_dir = os.path.join(OUTPUT_FOLDER, str(uuid.uuid4()))
        os.makedirs(out_dir, exist_ok=True)

        # (4) メタデータ取得
        video_processor = VideoProcessor()
        video_metadata = video_processor.get_video_metadata(processed_path)
        logger.info(f"動画メタデータ: {video_metadata}")

        # (5) ポーズ検出
        pose_detector = PoseDetector()
        pose_results = pose_detector.detect_poses(processed_path, out_dir)
        logger.info(f"ポーズ検出フレーム数: {len(pose_results)}")

        # (6) サーブフェーズ検出
        from services.motion_analyzer import ServePhase
        total_frames = len(pose_results)
        phase_duration = total_frames // 6 if total_frames else 1
        phase_names = [
            'preparation', 'ball_toss', 'trophy_position',
            'acceleration', 'contact', 'follow_through'
        ]
        serve_phases = []
        for i, name in enumerate(phase_names):
            start_frame = i * phase_duration
            end_frame = min((i + 1) * phase_duration, total_frames)
            duration = (end_frame - start_frame) / video_metadata.get('fps', 30)
            serve_phases.append(ServePhase(
                name=name, start_frame=start_frame,
                end_frame=end_frame, duration=duration, key_events=[]
            ))

        # (7) 動作解析
        motion_analyzer = MotionAnalyzer()
        analysis_result = motion_analyzer.analyze_motion(
            pose_results, serve_phases, video_metadata
        )

        # (8) 段階的評価
        tiered_evaluation = motion_analyzer.calculate_tiered_overall_score(analysis_result)
        analysis_result['tiered_evaluation'] = tiered_evaluation

        # (9) アドバイス生成パート（セキュア/有料プランのみAIアドバイス）
        is_premium = request.form.get("is_premium", "false").lower() == "true"
        user_concerns = request.form.get("user_concerns", "")
        language = request.form.get('language', 'ja')  # デフォルトは日本語
            # ここで language をログに出したり
        print(f"ユーザー選択言語: {language}")
        advice_generator = AdviceGenerator()  # ←APIキーはインスタンス生成時に環境変数から取得
        advice = advice_generator.generate_advice(
            analysis_data=analysis_result,
            user_concerns=user_concerns,
            language=language, 
            user_level="intermediate",
            use_chatgpt=is_premium,
            # api_keyは一切渡さない！（環境変数のみで運用）
        )
        analysis_result['advice'] = advice

        # (10) オーバーレイ画像生成
        overlay_images = generate_overlay_images_with_dominant_hand(
            processed_path, pose_results, out_dir, pose_detector
        )
        analysis_result['overlay_images'] = [
            '/' + os.path.relpath(img_path, start=os.path.dirname(__file__)).replace('\\', '/')
            for img_path in overlay_images
        ]

        if 'phase_analysis' in analysis_result:
            analysis_result['phase_scores'] = {k: v['score'] for k, v in analysis_result['phase_analysis'].items()}

        logger.info(f"生成オーバーレイ画像: {overlay_images}")

        return jsonify({'success': True, 'result': analysis_result})

    except Exception as e:
        logger.error(f"解析エラー: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/download/<filename>")
def download_file(filename):
    """アップロード/生成ファイルDL用（デバッグ用）"""
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# クリーンアップの有効期限（本番は24時間）
EXPIRE_SECONDS = 24 * 60 * 60

@app.route("/api/list_uploads", methods=["GET"])
def list_uploads():
    """アップロード済みファイル一覧を返す"""
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/list_output", methods=["GET"])
def list_output():
    """出力済みファイル一覧を返す"""
    try:
        files = []
        for root, dirs, filenames in os.walk(OUTPUT_FOLDER):
            for name in filenames:
                path = os.path.join(root, name)
                size = os.path.getsize(path)
                files.append({
                    "name": name,
                    "size": size,
                    "path": os.path.relpath(path, OUTPUT_FOLDER)
                })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/cleanup", methods=["POST"])
def cleanup_endpoint():
    """期限切れファイルの削除"""
    now = time.time()
    deleted = []

    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                try:
                    diff = now - os.path.getmtime(path)
                    if diff > EXPIRE_SECONDS:
                        os.remove(path)
                        deleted.append(path)
                except Exception as e:
                    deleted.append(f"削除エラー {path}: {e}")
            for name in dirs:
                path = os.path.join(root, name)
                try:
                    if now - os.path.getmtime(path) > EXPIRE_SECONDS:
                        shutil.rmtree(path)
                        deleted.append(path)
                except Exception as e:
                    deleted.append(f"削除エラー {path}: {e}")

    return jsonify({"deleted": deleted})

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, debug=True)
