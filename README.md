# H3 Musubi RunPod

RunPod container recipe for MiniMax H3 LoRA training with
`diodiogod/musubi-tuner_simple_GUI`.

## Pinned stack

- Base: `runpod/pytorch:1.0.3-cu1300-torch291-ubuntu2404`
- CUDA: 13.0
- PyTorch: 2.9.1
- Musubi commit: `ee845c7659ff7a505c905388310cdf488460184e`

## RunPod-specific fixes

The upstream GUI uses native Windows/Tk dialogs for Browse and Add Dataset.
Those controls do not work on a headless RunPod. This image patches them so
they ask for a path inside the Pod instead, e.g.:

`/workspace/datasets/my_character`

Musubi itself stays on localhost. An nginx reverse proxy with Basic Auth is
exposed on port 8677.

## Persistent folders

- `/workspace/datasets`
- `/workspace/models`
- `/workspace/output`
- `/workspace/cache`
- `/workspace/logs`
- `/workspace/projects`

## Published image

GitHub Actions publishes:

`ghcr.io/lokitsar/h3-musubi-runpod:v1.0.0`

Prefer the versioned tag in RunPod.

## RunPod template

- Template type: Pods
- Compute: NVIDIA / GPU
- Container image: `ghcr.io/lokitsar/h3-musubi-runpod:v1.0.0`
- Container disk: 40 GB minimum
- Persistent volume: 100 GB or more
- Persistent mount path: `/workspace`

Expose:

- `8677/http` — Musubi Studio
- `8888/http` — Jupyter Lab
- `22/tcp` — SSH/SCP/SFTP

Recommended environment variables:

- `MUSUBI_USER=musubi`
- `MUSUBI_PASSWORD=<strong password>`
- `JUPYTER_PASSWORD=<strong token/password>`
- `PUBLIC_KEY=<SSH public key>` if RunPod does not inject it automatically

If `MUSUBI_PASSWORD` is omitted, one is generated and stored in
`/workspace/MUSUBI_LOGIN.txt`.
