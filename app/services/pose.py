from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

try:
    import mediapipe as mp  # type: ignore
except Exception:  # pragma: no cover
    mp = None


LANDMARK_NAMES = [
    # 33 MediaPipe Pose landmarks (subset + names for readability)
    "nose", "left_eye_inner", "left_eye", "left_eye_outer", "right_eye_inner",
    "right_eye", "right_eye_outer", "left_ear", "right_ear", "mouth_left",
    "mouth_right", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky", "left_index",
    "right_index", "left_thumb", "right_thumb", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle", "left_heel",
    "right_heel", "left_foot_index", "right_foot_index",
]


class PoseEstimator:
    def __init__(self) -> None:
        if mp is None:
            raise RuntimeError("mediapipe non disponibile")
        self._pose = mp.solutions.pose.Pose(static_image_mode=False, model_complexity=1)

    def process(self, frame_bgr: np.ndarray) -> Tuple[Dict[str, dict], float]:
        # MediaPipe richiede RGB
        frame_rgb = frame_bgr[..., ::-1]
        results = self._pose.process(frame_rgb)
        keypoints: Dict[str, dict] = {}
        quality = 0.0
        if results.pose_landmarks:
            lms = results.pose_landmarks.landmark
            count = min(len(lms), len(LANDMARK_NAMES))
            for i in range(count):
                kp = lms[i]
                keypoints[LANDMARK_NAMES[i]] = {
                    "x": float(kp.x),
                    "y": float(kp.y),
                    "z": float(kp.z),
                    "visibility": float(kp.visibility),
                }
                quality += float(kp.visibility)
            if count:
                quality /= count
        return keypoints, quality

    def derive_angles(self, kps: Dict[str, dict]) -> Dict[str, float]:
        def angle(a, b, c) -> float:
            if a not in kps or b not in kps or c not in kps:
                return 0.0
            A = np.array([kps[a]["x"], kps[a]["y"]], dtype=float)
            B = np.array([kps[b]["x"], kps[b]["y"]], dtype=float)
            C = np.array([kps[c]["x"], kps[c]["y"]], dtype=float)
            BA = A - B
            BC = C - B
            num = float(np.dot(BA, BC))
            den = float(np.linalg.norm(BA) * np.linalg.norm(BC) + 1e-6)
            val = np.clip(num / den, -1.0, 1.0)
            return float(np.degrees(np.arccos(val)))

        return {
            "left_elbow": angle("left_shoulder", "left_elbow", "left_wrist"),
            "right_elbow": angle("right_shoulder", "right_elbow", "right_wrist"),
            "left_knee": angle("left_hip", "left_knee", "left_ankle"),
            "right_knee": angle("right_hip", "right_knee", "right_ankle"),
        }

    def derive_symmetry(self, kps: Dict[str, dict]) -> Dict[str, float]:
        val = 0.0
        if "left_shoulder" in kps and "right_shoulder" in kps:
            val = 1.0 - abs(kps["left_shoulder"]["y"] - kps["right_shoulder"]["y"])
        return {"shoulders": float(np.clip(val, 0.0, 1.0))}

