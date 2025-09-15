from pathlib import Path
import cv2
import numpy as np

def generate_overlay_images_with_dominant_hand(
    video_path, pose_results, output_dir, pose_detector
):
    """
    pose_results から利き腕を自動判定し、
    5枚のオーバーレイ画像（PoseDetectorでランドマーク描画）を保存してパスリストを返す
    ※フレーム間引き対応・IndexError絶対出ない安全設計
    """

    # 利き手自動判定
    right_hand_raised = 0
    left_hand_raised = 0

    for result in pose_results:
        if result.get("has_pose"):
            rw = result["landmarks"].get("right_wrist", {})
            lw = result["landmarks"].get("left_wrist", {})
            rs = result["landmarks"].get("right_shoulder", {})
            ls = result["landmarks"].get("left_shoulder", {})
            if all([rw, rs]) and rw.get("y", 1) < rs.get("y", 1):
                right_hand_raised += 1
            if all([lw, ls]) and lw.get("y", 1) < ls.get("y", 1):
                left_hand_raised += 1

    dominant_hand = "right" if right_hand_raised >= left_hand_raised else "left"
    print(f"🟢 利き手判定: {dominant_hand}")

    # トロフィーポーズ検出
    candidate_frames = []
    for result in pose_results:
        if result.get("has_pose"):
            wrist = result["landmarks"].get(f"{dominant_hand}_wrist", {})
            elbow = result["landmarks"].get(f"{dominant_hand}_elbow", {})
            shoulder = result["landmarks"].get(f"{dominant_hand}_shoulder", {})
            if all([wrist, elbow, shoulder]):
                if (elbow["y"] < shoulder["y"]) and (wrist["y"] < shoulder["y"]):
                    candidate_frames.append((result["frame_number"], wrist["y"]))

    # === フレーム選択方針（候補なければ等間隔）===
    if candidate_frames:
        candidate_frames.sort(key=lambda x: x[1])
        trophy_frame = candidate_frames[0][0]
        window = 30
        start_frame = max(trophy_frame - window, 0)
        end_frame = trophy_frame + window
        raw_frame_indices = np.linspace(start_frame, end_frame, num=5, dtype=int).tolist()
    else:
        # 元動画全体で等間隔
        if pose_results:
            max_frame_number = max(r.get("frame_number", 0) for r in pose_results)
        else:
            max_frame_number = 0
        raw_frame_indices = np.linspace(0, max_frame_number, num=5, dtype=int).tolist()

    # === 「一番近い解析済みフレーム」を選ぶマッピング ===
    frame_number_to_result = {r["frame_number"]: r for r in pose_results}
    available_frames = sorted(frame_number_to_result.keys())
    selected_pose_results = []
    for target in raw_frame_indices:
        # 解析済みframe_numberのうち一番近いものを選ぶ
        if not available_frames:
            continue
        nearest = min(available_frames, key=lambda x: abs(x - target))
        selected_pose_results.append((nearest, frame_number_to_result[nearest]))

    # === 動画から実際の画像フレーム取得と保存 ===
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"動画を開けません: {video_path}")

    saved_images = []
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for idx, (frame_no, pose_data) in enumerate(selected_pose_results):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            continue
        annotated_frame = pose_detector._draw_pose_landmarks(frame, pose_data)
        filename = f"pose_{idx:03d}.jpg"
        save_path = Path(output_dir) / filename
        cv2.imwrite(str(save_path), annotated_frame)
        saved_images.append(str(save_path))
    cap.release()
    return [str(p) for p in saved_images]
