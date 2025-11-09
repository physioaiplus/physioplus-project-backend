from fastapi import APIRouter
from ..schemas import ApiResponse
from ..services.camera import camera


router = APIRouter()


@router.post("/start")
def start_camera() -> ApiResponse:
    ok, msg = camera.start()
    return ApiResponse(success=ok, message=msg)


@router.post("/stop")
def stop_camera() -> ApiResponse:
    ok, msg = camera.stop()
    return ApiResponse(success=ok, message=msg)


@router.get("/status")
def camera_status() -> ApiResponse:
    return ApiResponse(success=True, data=camera.status())

