#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

needle = """async function api(path, options = {}) {
  const response = await fetch(path, { headers: {\"Content-Type\":\"application/json\", ...(options.headers || {})}, ...options });"""

replacement = """async function api(path, options = {}) {
  // RunPod is headless. Replace native desktop path dialogs with a browser
  // prompt for paths that exist inside the Pod.
  if (path === \"/api/path/select\") {
    let body = {};
    try { body = JSON.parse(options.body || \"{}\"); } catch (_) {}
    const isDirectory = body.kind === \"directory\";
    let fallback = body.initial || (isDirectory ? \"/workspace\" : \"/workspace/projects/dataset.toml\");\n    if (!isDirectory && /^\\/workspace\\/projects\\/?$/.test(String(fallback))) fallback = \"/workspace/projects/dataset.toml\";
    // Never present an inherited Windows path on a Linux RunPod.
    if (/^[A-Za-z]:[\\\\/]/.test(String(fallback))) {
      fallback = isDirectory ? \"/workspace\" : \"/workspace/projects/dataset.toml\";
    }
    const selected = window.prompt(
      isDirectory
        ? \"Enter a directory path on this RunPod:\"
        : \"Enter a file path on this RunPod:\",
      fallback
    );
    return {path: selected ? selected.trim() : \"\"};
  }
  if (path === \"/api/path/drop\") {
    const selected = window.prompt(
      \"Enter the dataset folder path on this RunPod:\",
      \"/workspace/datasets\"
    );
    const clean = selected ? selected.trim() : \"\";
    return {paths: clean ? [clean] : [], path: clean};
  }

  const response = await fetch(path, { headers: {\"Content-Type\":\"application/json\", ...(options.headers || {})}, ...options });"""

if needle not in text:
    raise SystemExit("Could not locate api() function in pinned Musubi app.js.")

path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
print(f"Patched headless RunPod path selection in {path}")
