import os
from fastapi import APIRouter

from ..schemas import ApiResponse
from ..services.camera import camera


router = APIRouter()


@router.get("/api/status")
def backend_status() -> ApiResponse:
    # Verifica disponibilità MediaPipe
    try:
        from ..services.pose import PoseEstimator  # type: ignore

        pose_available = True
        # Istanziazione facoltativa per ulteriore verifica
        try:
            _ = PoseEstimator()  # noqa: F841
        except Exception:
            pose_available = False
    except Exception:
        pose_available = False

    # Verifica disponibilità SMPL
    try:
        from ..services.smpl import SmplFitter

        smpl = SmplFitter()
        smpl_available = bool(smpl.available)
        smpl_model_dir = smpl.model_dir
    except Exception:
        smpl_available = False
        smpl_model_dir = os.getenv("SMPL_MODEL_DIR")

    data = {
        "version": "0.1.0",
        "pose_available": pose_available,
        "smpl_available": smpl_available,
        "smpl_model_dir": smpl_model_dir,
        "camera": camera.status(),
        "ws_endpoints": {
            "pose_stream": "/ws/pose-stream/{visit_id}",
        },
    }
    return ApiResponse(success=True, data=data)

