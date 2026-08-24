# Musubi RunPod v1.0.3

A RunPod-focused wrapper around the pinned Musubi Simple GUI fork. It keeps Musubi's trainers intact while removing most of the desktop-filesystem friction from H3 and Krea 2 training.

## Normal workflow

1. Deploy the RunPod template.
2. Open Jupyter on port 8888.
3. Upload a dataset folder to `/workspace/datasets/<name>` with matching `.txt` sidecars when captions are used.
4. Open Musubi on port 8677.
5. Choose MiniMax H3 or Krea 2. Missing model bundles are offered on demand.
6. In New training -> Dataset, choose the uploaded folder from **RunPod quick dataset** and click **Use dataset**.
7. Musubi automatically creates or reuses `/workspace/projects/<name>.toml`, selects it in the recipe, and loads it in the visual Dataset workspace.
8. Review settings and train.

No giant model download happens merely because the pod starts.

## v1.0.3 workflow fixes

- Scans `/workspace/datasets` automatically.
- Adds a dataset picker directly to New training -> Dataset.
- Adds a quick dataset list to the Dataset workspace.
- Creates a sensible 1024px, batch-1, bucketed TOML automatically for new image/video folders.
- Reuses existing TOMLs instead of overwriting them.
- Stores caches under `/workspace/cache/<dataset>`.
- Automatically sets the training recipe's `dataset_config` to the generated TOML.
- Fixes **Save TOML** so changing only the destination filename/path enables Save As.
- Improves the headless file picker default to `/workspace/projects/dataset.toml` instead of a bare directory.
- Replaces the misleading **Configure Accelerate** card with a RunPod environment-ready explanation. Accelerate remains installed and usable; normal single-GPU training does not require manual configuration.

## Model bundles

### MiniMax H3
On-demand bundle under `/workspace/models/h3`:
- compact pruned INT8 ConvRot FL2VA DiT
- compact Qwen3-VL-32B text encoder
- H3 FP16 video VAE

### Krea 2
On-demand bundle under `/workspace/models/krea2`:
- `krea/Krea-2-Raw/raw.safetensors`
- Qwen3-VL text encoder
- Qwen-Image VAE

Krea-2 Raw is gated. Add `HF_TOKEN` as a RunPod secret and ensure that Hugging Face account has access to `krea/Krea-2-Raw`.

## RunPod template

Container image after GitHub Actions succeeds:

`ghcr.io/lokitsar/h3-musubi-runpod:v1.0.3`

Ports:
- HTTP 8677 - Musubi
- HTTP 8888 - JupyterLab
- TCP 22 - SSH

Persistent volume:
- `/workspace`
- 150 GB recommended when keeping H3 + Krea2 models and multiple datasets

Environment:
- `MUSUBI_USER=musubi`
- `MUSUBI_PASSWORD=<RunPod secret>`
- `JUPYTER_PASSWORD=<RunPod secret>`
- `PUBLIC_KEY=<SSH public key>`
- `HF_TOKEN=<RunPod secret>` only when Krea 2 downloads are needed

Leave the RunPod **Start command blank**. The image intentionally inherits RunPod's native startup so Jupyter and SSH work normally.
