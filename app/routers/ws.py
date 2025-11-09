import asyncio
import base64
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.camera import camera


router = APIRouter()


@router.websocket("/ws/pose-stream/{visit_id}")
async def pose_stream(ws: WebSocket, visit_id: str):
    await ws.accept()
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                # Send a tiny 1x1 transparent pixel if no frame
                img_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82").decode("ascii")
            else:
                img_b64 = camera.frame_to_base64(frame)

            analysis = camera.analyze()
            payload = {
                "frame": f"data:image/jpeg;base64,{img_b64}",
                "analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "visit_id": visit_id,
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        # Client disconnected gracefully
        return
