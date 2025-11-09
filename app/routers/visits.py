import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Body

from ..schemas import ApiResponse, Visit


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "visits")
os.makedirs(DATA_DIR, exist_ok=True)


router = APIRouter()


def _visit_path(visit_id: str) -> str:
    return os.path.abspath(os.path.join(DATA_DIR, f"{visit_id}.json"))


@router.post("")
def create_visit(payload: dict = Body(...)) -> ApiResponse:
    visit_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    visit = Visit(
        id=visit_id,
        patient_id=payload.get("patient_id", ""),
        operator_id=payload.get("operator_id", ""),
        tipo_analisi=payload.get("tipo_analisi", "completa"),
        status="in_progress",
        note=payload.get("note", ""),
        created_at=now,
        exercises=[],
    )
    with open(_visit_path(visit_id), "w", encoding="utf-8") as f:
        json.dump(visit.model_dump(), f, ensure_ascii=False, indent=2)
    return ApiResponse(success=True, data={"visit_id": visit_id})


@router.get("/{visit_id}")
def get_visit(visit_id: str) -> ApiResponse:
    path = _visit_path(visit_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ApiResponse(success=True, data=data)
    return ApiResponse(success=False, message="Visit not found")


@router.put("/{visit_id}/exercises")
def update_exercises(visit_id: str, exercises: List[Any] = Body(...)) -> ApiResponse:
    path = _visit_path(visit_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "id": visit_id,
            "patient_id": "",
            "operator_id": "",
            "tipo_analisi": "completa",
            "status": "in_progress",
            "note": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "exercises": [],
        }

    data["exercises"] = exercises
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return ApiResponse(success=True)

