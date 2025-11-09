import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict


VISITS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "visits"))
os.makedirs(VISITS_DIR, exist_ok=True)


def _visit_path(visit_id: str) -> str:
    return os.path.join(VISITS_DIR, f"{visit_id}.json")


def create_visit(payload: Dict[str, Any]) -> str:
    visit_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "id": visit_id,
        "patient_id": payload.get("patient_id", ""),
        "operator_id": payload.get("operator_id", ""),
        "tipo_analisi": payload.get("tipo_analisi", "completa"),
        "status": "in_progress",
        "note": payload.get("note", ""),
        "created_at": now,
        "exercises": [],
    }
    with open(_visit_path(visit_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return visit_id


def get_visit(visit_id: str) -> Optional[Dict[str, Any]]:
    path = _visit_path(visit_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_exercises(visit_id: str, exercises: List[Any]) -> bool:
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
    return True

