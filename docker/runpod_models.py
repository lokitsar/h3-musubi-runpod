from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download

MODEL_ROOT = Path(os.environ.get("RUNPOD_MODEL_ROOT", "/workspace/models")).expanduser()

BUNDLES: dict[str, dict[str, Any]] = {
    "MiniMax H3 (Experimental)": {
        "label": "MiniMax H3",
        "size_note": "about 42 GB",
        "requires_hf_token": False,
        "root": MODEL_ROOT / "h3",
        "files": [
            {"repo": "Comfy-Org/MiniMax-H3", "filename": "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", "setting": "minimax_h3_dit_model"},
            {"repo": "Comfy-Org/MiniMax-H3", "filename": "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "setting": "minimax_h3_text_encoder"},
            {"repo": "Comfy-Org/MiniMax-H3", "filename": "vae/minimax_h3_video_vae_fp16.safetensors", "setting": "vae_model"},
        ],
        "extra_settings": {"minimax_h3_tokenizer": "MiniMaxAI/MiniMax-H3"},
    },
    "Krea 2": {
        "label": "Krea 2",
        "size_note": "about 34 GB",
        "requires_hf_token": True,
        "root": MODEL_ROOT / "krea2",
        "files": [
            {"repo": "krea/Krea-2-Raw", "filename": "raw.safetensors", "setting": "krea2_dit_model", "gated": True},
            {"repo": "Comfy-Org/Qwen3-VL", "filename": "text_encoders/qwen3vl_4b_bf16.safetensors", "setting": "krea2_text_encoder"},
            {"repo": "Comfy-Org/Qwen-Image_ComfyUI", "filename": "split_files/vae/qwen_image_vae.safetensors", "setting": "vae_model"},
        ],
        "extra_settings": {"krea2_turbo_dit": ""},
    },
}


def _bundle(mode: str) -> dict[str, Any]:
    if mode not in BUNDLES:
        raise ValueError(f"No RunPod model bundle is defined for {mode!r}.")
    return BUNDLES[mode]


def _target(bundle: dict[str, Any], item: dict[str, Any]) -> Path:
    return Path(bundle["root"]) / item["filename"]


def settings_patch(mode: str) -> dict[str, Any]:
    bundle = _bundle(mode)
    patch = dict(bundle.get("extra_settings") or {})
    for item in bundle["files"]:
        patch[item["setting"]] = str(_target(bundle, item))
    return patch


def bundle_status(mode: str) -> dict[str, Any]:
    bundle = _bundle(mode)
    missing = []
    files = []
    for item in bundle["files"]:
        target = _target(bundle, item)
        present = target.is_file() and target.stat().st_size > 0
        files.append({"path": str(target), "present": present, "repo": item["repo"], "filename": item["filename"]})
        if not present:
            missing.append(str(target))
    return {
        "mode": mode,
        "label": bundle["label"],
        "ready": not missing,
        "missing": missing,
        "files": files,
        "size_note": bundle["size_note"],
        "requires_hf_token": bool(bundle.get("requires_hf_token")),
        "settings_patch": settings_patch(mode),
    }


def ensure_bundle(mode: str) -> dict[str, Any]:
    bundle = _bundle(mode)
    root = Path(bundle["root"])
    root.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for item in bundle["files"]:
        target = _target(bundle, item)
        if target.is_file() and target.stat().st_size > 0:
            continue
        if item.get("gated") and not os.environ.get("HF_TOKEN"):
            raise RuntimeError(
                "Krea-2 Raw is gated on Hugging Face. Add HF_TOKEN as a RunPod secret and make sure that Hugging Face account has accepted access to krea/Krea-2-Raw."
            )
        print(f"[model-manager] Downloading {item['repo']} :: {item['filename']}", flush=True)
        try:
            resolved = hf_hub_download(
                repo_id=item["repo"],
                filename=item["filename"],
                local_dir=str(root),
                token=os.environ.get("HF_TOKEN") or None,
            )
        except Exception as exc:
            if item.get("gated"):
                raise RuntimeError(
                    "Could not download gated Krea-2 Raw. Confirm HF_TOKEN is valid and its Hugging Face account has access to krea/Krea-2-Raw."
                ) from exc
            raise
        downloaded.append(str(resolved))
    result = bundle_status(mode)
    result["downloaded"] = downloaded
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="RunPod Musubi model-bundle manager")
    parser.add_argument("action", choices=["status", "download"])
    parser.add_argument("mode", choices=list(BUNDLES))
    args = parser.parse_args()
    result = bundle_status(args.mode) if args.action == "status" else ensure_bundle(args.mode)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
