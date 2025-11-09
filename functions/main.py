import json
import os
from typing import Any

from firebase_functions import https_fn

from backend.camera_service import camera as camera_manager
from backend.visits_storage import create_visit, get_visit, update_exercises
from backend.results_service import finalize as finalize_visit, get_results as load_results, mesh_path


def _json_response(obj: Any, status: int = 200) -> https_fn.Response:
    return https_fn.Response(json.dumps(obj), mimetype="application/json", status=status)


@https_fn.on_request()
def camera_start(req: https_fn.Request) -> https_fn.Response:
    if req.method != "POST":
        return _json_response({"success": False, "message": "Method not allowed"}, 405)
    ok, msg = camera_manager.start()
    return _json_response({"success": ok, "message": msg})


@https_fn.on_request()
def camera_stop(req: https_fn.Request) -> https_fn.Response:
    if req.method != "POST":
        return _json_response({"success": False, "message": "Method not allowed"}, 405)
    ok, msg = camera_manager.stop()
    return _json_response({"success": ok, "message": msg})


@https_fn.on_request()
def camera_status(req: https_fn.Request) -> https_fn.Response:
    data = camera_manager.status()
    return _json_response({"success": True, "data": data})


@https_fn.on_request()
def visits_create(req: https_fn.Request) -> https_fn.Response:
    if req.method != "POST":
        return _json_response({"success": False, "message": "Method not allowed"}, 405)
    payload = req.get_json(silent=True) or {}
    vid = create_visit(payload)
    return _json_response({"success": True, "data": {"visit_id": vid}})


@https_fn.on_request()
def visits_get(req: https_fn.Request) -> https_fn.Response:
    # Expected query param: ?id=<visit_id>
    visit_id = req.args.get("id") if hasattr(req, "args") else None
    if not visit_id:
        return _json_response({"success": False, "message": "Missing id"}, 400)
    data = get_visit(visit_id)
    if not data:
        return _json_response({"success": False, "message": "Visit not found"}, 404)
    return _json_response({"success": True, "data": data})


@https_fn.on_request()
def visits_update_exercises(req: https_fn.Request) -> https_fn.Response:
    if req.method != "PUT":
        return _json_response({"success": False, "message": "Method not allowed"}, 405)
    visit_id = req.args.get("id") if hasattr(req, "args") else None
    if not visit_id:
        return _json_response({"success": False, "message": "Missing id"}, 400)
    exercises = req.get_json(silent=True) or []
    update_exercises(visit_id, exercises)
    return _json_response({"success": True})


@https_fn.on_request()
def visits_finalize(req: https_fn.Request) -> https_fn.Response:
    if req.method != "POST":
        return _json_response({"success": False, "message": "Method not allowed"}, 405)
    visit_id = req.args.get("id") if hasattr(req, "args") else None
    if not visit_id:
        return _json_response({"success": False, "message": "Missing id"}, 400)
    ok, data = finalize_visit(visit_id, camera_manager)
    return _json_response({"success": ok, "data": data})


@https_fn.on_request()
def results_get(req: https_fn.Request) -> https_fn.Response:
    visit_id = req.args.get("id") if hasattr(req, "args") else None
    if not visit_id:
        return _json_response({"success": False, "message": "Missing id"}, 400)
    data = load_results(visit_id)
    if not data:
        return _json_response({"success": False, "message": "Results not found"}, 404)
    return _json_response({"success": True, "data": data})


@https_fn.on_request()
def results_mesh(req: https_fn.Request) -> https_fn.Response:
    visit_id = req.args.get("id") if hasattr(req, "args") else None
    if not visit_id:
        return _json_response({"success": False, "message": "Missing id"}, 400)
    path = mesh_path(visit_id)
    if not os.path.exists(path):
        return https_fn.Response("mesh not found", status=404)
    with open(path, "rb") as f:
        data = f.read()
    return https_fn.Response(data, mimetype="text/plain")


# Optional: consolidated status function (useful for UI checks)
@https_fn.on_request()
def backend_status(req: https_fn.Request) -> https_fn.Response:
    # Try to import PoseEstimator
    try:
        from backend.pose import PoseEstimator  # type: ignore

        pose_available = True
        try:
            _ = PoseEstimator()  # noqa: F841
        except Exception:
            pose_available = False
    except Exception:
        pose_available = False

    # SMPL availability
    try:
        from backend.smpl_fitter import SmplFitter

        smpl = SmplFitter()
        smpl_available = bool(smpl.available)
        smpl_model_dir = smpl.model_dir
    except Exception:
        smpl_available = False
        smpl_model_dir = os.getenv("SMPL_MODEL_DIR")

    return _json_response(
        {
            "success": True,
            "data": {
                "version": "0.1.0",
                "pose_available": pose_available,
                "smpl_available": smpl_available,
                "smpl_model_dir": smpl_model_dir,
                "camera": camera_manager.status(),
                "ws_endpoints": {"pose_stream": "/ws/pose-stream/{visit_id}"},
            },
        }
    )
