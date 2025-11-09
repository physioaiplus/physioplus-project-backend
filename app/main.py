from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.camera import router as camera_router
from .routers.visits import router as visits_router
from .routers.ws import router as ws_router
from .routers.results import router as results_router
from .routers.status import router as status_router


def create_app() -> FastAPI:
    app = FastAPI(title="PhysioPlus Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*", "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(camera_router, prefix="/api/camera", tags=["camera"])
    app.include_router(visits_router, prefix="/api/visits", tags=["visits"])
    app.include_router(ws_router, tags=["ws"])
    app.include_router(results_router, tags=["results"])
    app.include_router(status_router, tags=["status"]) 

    return app


app = create_app()
