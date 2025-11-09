import base64
import threading
from datetime import datetime, timezone
from typing import Optional, Tuple

import numpy as np

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # OpenCV opzionale

try:
    from .pose import PoseEstimator  # type: ignore
except Exception:
    PoseEstimator = None  # opzionale se mediapipe non disponibile


class CameraManager:
    def __init__(self) -> None:
        self._streaming = False
        self._cap = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self.width = 640
        self.height = 480
        self.fps = 10
        self._last_frame: Optional[np.ndarray] = None
        self._pose = PoseEstimator() if PoseEstimator is not None else None

    def start(self) -> Tuple[bool, str]:
        with self._lock:
            if self._streaming:
                return True, "Camera already running"
            if cv2 is None:
                # Modalità stub: nessuna webcam disponibile
                self._streaming = True
                self._thread = threading.Thread(target=self._loop_stub, daemon=True)
                self._thread.start()
                return True, "Camera started in stub mode"

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self._streaming = True
                self._thread = threading.Thread(target=self._loop_stub, daemon=True)
                self._thread.start()
                return True, "Camera fallback to stub (no device)"

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            self._cap = cap
            self._streaming = True
            self._thread = threading.Thread(target=self._loop_capture, daemon=True)
            self._thread.start()
            return True, "Camera started"

    def stop(self) -> Tuple[bool, str]:
        with self._lock:
            if not self._streaming:
                return True, "Camera already stopped"
            self._streaming = False
            if self._cap is not None and cv2 is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            return True, "Camera stopped"

    def status(self) -> dict:
        return {
            "streaming": self._streaming,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "backend": "opencv" if cv2 is not None else "stub",
        }

    def get_frame(self) -> Optional[np.ndarray]:
        return self._last_frame

    def frame_to_base64(self, frame: np.ndarray) -> str:
        if cv2 is not None:
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                return base64.b64encode(buf.tobytes()).decode("ascii")
        # fallback png via numpy if cv2 missing (very simple solid image)
        try:
            import PIL.Image as Image  # type: ignore
            from io import BytesIO

            im = Image.fromarray(frame[..., ::-1])  # BGR->RGB
            bio = BytesIO()
            im.save(bio, format="JPEG", quality=80)
            return base64.b64encode(bio.getvalue()).decode("ascii")
        except Exception:
            return ""

    def analyze(self) -> dict:
        # Se disponibile MediaPipe, usa l'estimatore reale
        if self._pose is not None and self._last_frame is not None:
            try:
                kps, quality = self._pose.process(self._last_frame)
                ts = datetime.now(timezone.utc).isoformat()
                angles = self._pose.derive_angles(kps)
                symmetry = self._pose.derive_symmetry(kps)
                return {
                    "keypoints": kps,
                    "angles": angles,
                    "symmetry": symmetry,
                    "timestamp": ts,
                    "frame_quality": quality,
                }
            except Exception:
                pass
        # Fallback fittizio se non disponibile
        ts = datetime.now(timezone.utc).isoformat()
        kp = {
            "nose": {"x": 0.5, "y": 0.2, "z": 0.0, "visibility": 0.9},
            "left_shoulder": {"x": 0.4, "y": 0.35, "z": 0.0, "visibility": 0.9},
            "right_shoulder": {"x": 0.6, "y": 0.35, "z": 0.0, "visibility": 0.9},
        }
        return {
            "keypoints": kp,
            "angles": {"shoulder_tilt": (kp["right_shoulder"]["y"] - kp["left_shoulder"]["y"]) * 10},
            "symmetry": {"shoulders": 1.0},
            "timestamp": ts,
            "frame_quality": 0.95,
        }

    # Internal loops
    def _loop_capture(self) -> None:
        assert cv2 is not None
        assert self._cap is not None
        while self._streaming:
            ok, frame = self._cap.read()
            if ok:
                self._last_frame = frame
            else:
                self._last_frame = self._solid_frame((255, 255, 255))
            if cv2 is not None:
                cv2.waitKey(int(1000 / max(self.fps, 1)))

    def _loop_stub(self) -> None:
        # Genera un frame statico di placeholder
        color = (40, 40, 40)
        text_color = (255, 255, 255)
        while self._streaming:
            frame = self._solid_frame(color)
            try:
                # draw STUB text if cv2 available
                if cv2 is not None:
                    cv2.putText(frame, "STUB STREAM", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, text_color, 2)
            except Exception:
                pass
            self._last_frame = frame
            # sleep approx fps
            if cv2 is not None:
                cv2.waitKey(int(1000 / max(self.fps, 1)))

    def _solid_frame(self, bgr: tuple) -> np.ndarray:
        return np.full((self.height, self.width, 3), bgr, dtype=np.uint8)


camera = CameraManager()
