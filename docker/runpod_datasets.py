from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import toml

IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp", ".avif", ".jxl"}
VIDEO_EXTENSIONS = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"}

WORKSPACE = Path(os.environ.get("RP_WORKSPACE", "/workspace")).expanduser().resolve()
PRIMARY_DATASET_ROOT = WORKSPACE / "datasets"
LEGACY_DATASET_ROOT = WORKSPACE / "dataset"
PROJECT_ROOT = WORKSPACE / "projects"
CACHE_ROOT = WORKSPACE / "cache"


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return value.lower() or "dataset"


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _media(path: Path) -> tuple[list[Path], list[Path]]:
    images, videos = [], []
    if not path.is_dir():
        return images, videos
    for item in path.iterdir():
        if not item.is_file():
            continue
        suffix = item.suffix.casefold()
        if suffix in IMAGE_EXTENSIONS:
            images.append(item)
        elif suffix in VIDEO_EXTENSIONS:
            videos.append(item)
    return sorted(images), sorted(videos)


def _caption_count(media: list[Path]) -> int:
    return sum(1 for item in media if item.with_suffix(".txt").is_file())


def _toml_source(path: Path) -> str:
    return str(path.resolve())


def _candidate_toml(path: Path) -> Path:
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    base = _slug(path.name)
    candidate = PROJECT_ROOT / f"{base}.toml"
    index = 2
    while candidate.exists():
        try:
            payload = toml.load(candidate)
            for dataset in payload.get("datasets", []):
                source = dataset.get("image_directory") or dataset.get("video_directory")
                if source and Path(str(source)).expanduser().resolve() == path.resolve():
                    return candidate
        except Exception:
            pass
        candidate = PROJECT_ROOT / f"{base}-{index}.toml"
        index += 1
    return candidate


def _entry(path: Path, root: Path) -> dict[str, Any] | None:
    images, videos = _media(path)
    media = images if images else videos
    if not media:
        return None
    kind = "image" if images else "video"
    captions = _caption_count(media)
    toml_path = _candidate_toml(path)
    return {
        "name": path.name or root.name,
        "path": str(path.resolve()),
        "kind": kind,
        "image_count": len(images),
        "video_count": len(videos),
        "media_count": len(media),
        "caption_count": captions,
        "caption_coverage": round((captions / len(media)) * 100) if media else 0,
        "toml_path": str(toml_path),
        "toml_exists": toml_path.is_file(),
        "legacy_root": root == LEGACY_DATASET_ROOT,
    }


def scan_datasets() -> dict[str, Any]:
    PRIMARY_DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in (PRIMARY_DATASET_ROOT, LEGACY_DATASET_ROOT):
        if not root.is_dir():
            continue
        candidates = [root]
        candidates.extend(sorted((item for item in root.iterdir() if item.is_dir()), key=lambda p: p.name.casefold()))
        for candidate in candidates:
            resolved = str(candidate.resolve())
            if resolved in seen:
                continue
            entry = _entry(candidate, root)
            if entry:
                seen.add(resolved)
                results.append(entry)

    results.sort(key=lambda item: (item["legacy_root"], item["name"].casefold()))
    return {
        "workspace": str(WORKSPACE),
        "dataset_root": str(PRIMARY_DATASET_ROOT),
        "project_root": str(PROJECT_ROOT),
        "datasets": results,
    }


def use_dataset(path_value: str) -> dict[str, Any]:
    if not str(path_value or "").strip():
        raise ValueError("Choose a dataset folder.")
    path = Path(path_value).expanduser().resolve()
    allowed = any(_is_inside(path, root.resolve()) for root in (PRIMARY_DATASET_ROOT, LEGACY_DATASET_ROOT) if root.exists())
    if not allowed:
        raise PermissionError(f"RunPod quick datasets must be inside {PRIMARY_DATASET_ROOT}.")

    images, videos = _media(path)
    media = images if images else videos
    if not media:
        raise ValueError(f"No supported image or video files were found directly inside {path}.")

    kind = "image" if images else "video"
    captions = _caption_count(media)
    toml_path = _candidate_toml(path)
    created = False

    if not toml_path.exists():
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        cache_dir = CACHE_ROOT / _slug(path.name)
        cache_dir.mkdir(parents=True, exist_ok=True)

        general = {
            "resolution": 1024,
            "batch_size": 1,
            "enable_bucket": True,
            "bucket_no_upscale": False,
        }
        dataset: dict[str, Any] = {
            f"{kind}_directory": _toml_source(path),
            "num_repeats": 1,
            "cache_directory": str(cache_dir),
        }
        if captions:
            dataset["caption_extension"] = ".txt"

        text = toml.dumps({"general": general, "datasets": [dataset]})
        temp = toml_path.with_suffix(toml_path.suffix + ".tmp")
        temp.write_text(text, encoding="utf-8")
        temp.replace(toml_path)
        created = True

    entry = _entry(path, PRIMARY_DATASET_ROOT if _is_inside(path, PRIMARY_DATASET_ROOT.resolve()) else LEGACY_DATASET_ROOT)
    if entry is None:
        raise RuntimeError("Dataset disappeared while it was being prepared.")
    entry["toml_path"] = str(toml_path)
    entry["toml_exists"] = True
    entry["created"] = created
    return entry
