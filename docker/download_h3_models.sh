#!/usr/bin/env bash
set -euo pipefail

ROOT="${H3_MODEL_ROOT:-/workspace/models/h3}"
PYTHON="${MUSUBI_HOME:-/opt/musubi}/venv/bin/python"

mkdir -p "${ROOT}/diffusion_models" "${ROOT}/text_encoders" "${ROOT}/vae"

H3_MODEL_ROOT="${ROOT}" "${PYTHON}" - <<'PY'
from pathlib import Path
from huggingface_hub import hf_hub_download
import os

root = Path(os.environ.get("H3_MODEL_ROOT", "/workspace/models/h3"))
repo = "Comfy-Org/MiniMax-H3"
files = [
    "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "vae/minimax_h3_video_vae_fp16.safetensors",
]

for filename in files:
    target = root / filename
    if target.is_file() and target.stat().st_size > 0:
        print(f"[exists] {target}")
        continue
    print(f"[download] {filename}")
    path = hf_hub_download(repo_id=repo, filename=filename, local_dir=str(root))
    print(f"[saved] {path}")

print("H3 model bundle ready.")
PY
