# physioplus-project-backend

Backend FastAPI allineato al frontend “physioplus-project” (Humotion).

Obiettivi principali:
- Endpoints REST compatibili con `API_ENDPOINTS` del frontend
- WebSocket `/ws/pose-stream/{visit_id}` che invia `StreamData`
- Gestione camera lato backend (start/stop/status)
- Endpoint esercizi visita (stub persistente su file)

## Requisiti

- Python 3.9+
- (Opzionale) OpenCV per stream reale dalla webcam
- (Opzionale) MediaPipe Pose per keypoint: `pip install mediapipe`
- (Opzionale) SMPLX + Torch per ricostruzione mesh:
  - `pip install torch smplx`
  - Scarica i modelli SMPL/SMPLX (licenza richieste) e imposta `SMPL_MODEL_DIR` alla cartella che contiene le sottocartelle `smpl/` e/o `smplx/` (es.: `models/`).

## Installazione

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Avvio sviluppo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints principali

- `POST /api/camera/start` → { success }
- `POST /api/camera/stop` → { success }
- `GET  /api/camera/status` → { success, data: { streaming, width, height, fps } }
- `PUT  /api/visits/{id}/exercises` → { success }
- `GET  /api/visits/{id}` → { success, data: Visit }
- `POST /api/visits` → { success, data: { visit_id } }
- `POST /api/visits/{id}/finalize` → { success, data: { visit_id } }
- `GET  /api/results/{id}` → { success, data: { smpl, metrics, assets.mesh_url } }
- `GET  /api/results/{id}/mesh.obj` → OBJ placeholder
- `GET  /api/status` → { success, data: { pose_available, smpl_available, smpl_model_dir, camera, ws_endpoints } }
- `WS   /ws/pose-stream/{visit_id}` → Stream di `StreamData`

Nota: il fitting SMPL è stub (cubo OBJ). L’analisi pose inviata sul WS usa MediaPipe se installato; altrimenti è simulata. Integrare modelli reali in `app/services/pose.py` (MediaPipe) e `app/services/smpl.py` (SMPL).

### Integrazione reale (opzionale)
- MediaPipe Pose: installa `mediapipe` e il backend userà `PoseEstimator` per popolare `keypoints`, `angles`, `symmetry` in tempo reale.
- SMPL: installa `torch` e `smplx`, scarica i pesi ufficiali SMPL e imposta `SMPL_MODEL_DIR`. Il finalize genererà una mesh OBJ reale dal modello (pose neutra), con fallback al cubo se i modelli non sono disponibili.
