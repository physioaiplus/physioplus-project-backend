from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None


class Keypoint(BaseModel):
    x: float
    y: float
    z: float
    visibility: float = Field(ge=0.0, le=1.0)


class PostureAnalysis(BaseModel):
    keypoints: Dict[str, Keypoint]
    angles: Dict[str, float]
    symmetry: Dict[str, float]
    timestamp: str
    frame_quality: float


class StreamData(BaseModel):
    frame: str  # base64 PNG/JPEG
    analysis: PostureAnalysis
    timestamp: str
    visit_id: str


class Visit(BaseModel):
    id: str
    patient_id: str
    operator_id: str
    tipo_analisi: str
    status: str
    note: Optional[str] = None
    created_at: str
    exercises: List[dict] = []

