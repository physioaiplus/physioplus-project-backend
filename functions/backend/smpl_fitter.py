from __future__ import annotations

import os
from typing import Dict, Tuple, Optional


class SmplFitter:
    def __init__(self) -> None:
        self.available = False
        self._smplx = None
        self._torch = None
        self.model_dir: Optional[str] = None
        try:
            import smplx  # type: ignore
            import torch  # type: ignore

            self._smplx = smplx
            self._torch = torch
            # Individua directory modelli: env var o cartella locale 'models'
            self.model_dir = os.getenv("SMPL_MODEL_DIR") or os.path.abspath("models")
            if os.path.isdir(self.model_dir):
                self.available = True
        except Exception:
            self.available = False

    def fit(self, keypoints_2d: Dict[str, dict]) -> Tuple[Dict, str]:
        # Se SMPLX+Torch e modelli disponibili: genera mesh neutra reale
        if self.available:
            try:
                torch = self._torch  # type: ignore
                smplx = self._smplx  # type: ignore
                device = torch.device("cpu")
                model = smplx.create(
                    model_path=self.model_dir,  # cartella contenente subdir smpl/smplx
                    model_type="smpl",
                    gender="NEUTRAL",
                    use_pca=False,
                    batch_size=1,
                ).to(device)

                betas = torch.zeros([1, 10], device=device)
                body_pose = torch.zeros([1, 69], device=device)  # 23x3 axis-angle
                global_orient = torch.zeros([1, 3], device=device)
                transl = torch.zeros([1, 3], device=device)

                out = model(
                    betas=betas,
                    body_pose=body_pose,
                    global_orient=global_orient,
                    transl=transl,
                    pose2rot=True,
                )
                verts = out.vertices[0].detach().cpu().numpy()
                faces = model.faces

                params = {
                    "betas": betas.squeeze(0).tolist(),
                    "pose": (torch.cat([global_orient, body_pose], dim=1).squeeze(0).tolist()),
                    "transl": transl.squeeze(0).tolist(),
                }
                mesh_obj = self._to_obj(verts, faces)
                return params, mesh_obj
            except Exception:
                # Se qualcosa va storto, fallback al cubo
                pass

        # Fallback: ritorna cubo OBJ e parametri neutri
        params = {
            "betas": [0.0] * 10,
            "pose": [0.0] * 72,
            "transl": [0.0, 0.0, 0.0],
        }
        mesh_obj = self._cube_obj()
        return params, mesh_obj

    def _to_obj(self, vertices, faces) -> str:
        lines = ["# SMPL mesh", "o SMPL"]
        for v in vertices:
            lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        for f in faces:
            # OBJ usa indici 1-based
            lines.append(f"f {int(f[0])+1} {int(f[1])+1} {int(f[2])+1}")
        return "\n".join(lines)

    def _cube_obj(self) -> str:
        return "\n".join(
            [
                "# simple cube",
                "o Cube",
                "v -0.5 -0.5 -0.5",
                "v  0.5 -0.5 -0.5",
                "v  0.5  0.5 -0.5",
                "v -0.5  0.5 -0.5",
                "v -0.5 -0.5  0.5",
                "v  0.5 -0.5  0.5",
                "v  0.5  0.5  0.5",
                "v -0.5  0.5  0.5",
                "f 1 2 3 4",
                "f 5 6 7 8",
                "f 1 5 8 4",
                "f 2 6 7 3",
                "f 4 3 7 8",
                "f 1 2 6 5",
            ]
        )
