# H3 Musubi RunPod v1.0.1

A RunPod-friendly MiniMax H3 Musubi training image.

## What v1.0.1 fixes

- Keeps the official RunPod `/start.sh`, so SSH and JupyterLab use RunPod's native startup/proxy behavior.
- Starts Musubi automatically on HTTP port `8677`.
- Uses a standalone authenticated nginx instance for Musubi without modifying RunPod's nginx.
- Makes `accelerate` discoverable by Musubi.
- Installs the matching CUDA 13 `torchvision 0.24.1` wheel.
- Preserves the headless browser path picker fix.
- Replaces stale Windows defaults with `/workspace` H3 defaults.
- Creates standard persistent folders automatically.
- Adds `download-h3-models` for one-command H3 model setup.

## RunPod template

Image: `ghcr.io/lokitsar/h3-musubi-runpod:v1.0.1`

Recommended ports:
- `8677/http` — Musubi
- `8888/http` — JupyterLab
- `22/tcp` — SSH

Persistent mount: `/workspace`

Recommended environment variables:
- `MUSUBI_USER=musubi`
- `MUSUBI_PASSWORD=<RunPod secret>`
- `JUPYTER_PASSWORD=<RunPod secret>`
- `PUBLIC_KEY=<your SSH public key>`

Optional:
- `AUTO_DOWNLOAD_H3_MODELS=1` — downloads missing H3 model files at boot. This can take time and is not recommended on metered GPU time unless you intentionally want automatic setup.

## Normal workflow

1. Deploy the template.
2. Open Jupyter on port 8888 and upload the dataset into `/workspace/datasets/<name>`.
3. Open Musubi on port 8677.
4. Add the image folder, set caption extension `.txt`, and save the dataset TOML under `/workspace/projects`.
5. Start H3 training.

If the model bundle is missing, run this once in a terminal:

`download-h3-models`
