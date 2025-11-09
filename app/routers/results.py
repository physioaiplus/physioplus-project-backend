import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, FileResponse

from ..schemas import ApiResponse
from ..services.camera import camera
from ..services.smpl import SmplFitter


RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

router = APIRouter()


def _result_paths(visit_id: str) -> dict:
    base = os.path.abspath(os.path.join(RESULTS_DIR, visit_id))
    return {
        "params": base + ".json",
        "mesh": base + ".obj",
    }


@router.post("/api/visits/{visit_id}/finalize")
def finalize_visit(visit_id: str) -> ApiResponse:
    # Usa l'ultimo frame disponibile e i keypoint correnti (o stub)
    analysis = camera.analyze()
    fitter = SmplFitter()
    params, mesh_obj = fitter.fit(analysis.get("keypoints", {}))

    paths = _result_paths(visit_id)
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

    return ApiResponse(success=True, data={"visit_id": visit_id})


@router.get("/api/results/{visit_id}")
def get_results(visit_id: str) -> ApiResponse:
    paths = _result_paths(visit_id)
    if not os.path.exists(paths["params"]):
        return ApiResponse(success=False, message="Results not found")
    with open(paths["params"], "r", encoding="utf-8") as f:
        data: Any = json.load(f)
    return ApiResponse(success=True, data=data)


@router.get("/api/results/{visit_id}/mesh.obj")
def get_mesh_obj(visit_id: str):
    paths = _result_paths(visit_id)
    if not os.path.exists(paths["mesh"]):
        return PlainTextResponse("mesh not found", status_code=404)
    return FileResponse(paths["mesh"], media_type="text/plain")
