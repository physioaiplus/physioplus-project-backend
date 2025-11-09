import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from .camera_service import CameraManager
from .smpl_fitter import SmplFitter


RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
os.makedirs(RESULTS_DIR, exist_ok=True)


def _paths(visit_id: str) -> Dict[str, str]:
    base = os.path.abspath(os.path.join(RESULTS_DIR, visit_id))
    return {"params": base + ".json", "mesh": base + ".obj"}


def finalize(visit_id: str, camera: CameraManager) -> Tuple[bool, Dict[str, Any]]:
    analysis = camera.analyze()
    fitter = SmplFitter()
    params, mesh_obj = fitter.fit(analysis.get("keypoints", {}))
    paths = _paths(visit_id)
    with open(paths["params"], "w", encoding="utf-8") as f:
        json.dump(
            {
                "visit_id": visit_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "smpl_available": fitter.available,
                "smpl": params,
                "metrics": {
                    "angles": analysis.get("angles", {}),
                    "symmetry": analysis.get("symmetry", {}),
                },
                "assets": {"mesh_url": f"/api/results/{visit_id}/mesh.obj"},
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open(paths["mesh"], "w", encoding="utf-8") as f:
        f.write(mesh_obj)
    return True, {"visit_id": visit_id}


def get_results(visit_id: str) -> Dict[str, Any]:
    paths = _paths(visit_id)
    if not os.path.exists(paths["params"]):
        return {}
    with open(paths["params"], "r", encoding="utf-8") as f:
        return json.load(f)


def mesh_path(visit_id: str) -> str:
    return _paths(visit_id)["mesh"]

