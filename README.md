# Musubi RunPod v1.0.2

One RunPod template for MiniMax H3 and Krea 2 training.

## Normal flow
1. Deploy the template.
2. Open Jupyter on 8888 and upload a dataset to `/workspace/datasets`.
3. Open Musubi on 8677.
4. Select MiniMax H3 or Krea 2.
5. Musubi checks `/workspace/models` and offers to download only the selected trainer's missing model bundle.
6. Configure dataset and train.

Nothing large downloads just because the pod starts.

## H3 bundle
About 42 GB from `Comfy-Org/MiniMax-H3`:
- compact pruned INT8 ConvRot DiT
- compact Qwen3-VL-32B text encoder
- H3 FP16 video VAE

## Krea 2 bundle
About 34 GB:
- `krea/Krea-2-Raw/raw.safetensors`
- `Comfy-Org/Qwen3-VL/text_encoders/qwen3vl_4b_bf16.safetensors`
- `Comfy-Org/Qwen-Image_ComfyUI/split_files/vae/qwen_image_vae.safetensors`

Krea-2 Raw is gated. Add `HF_TOKEN` as a RunPod secret and ensure that Hugging Face account has accepted access to `krea/Krea-2-Raw`.

Krea-2 Turbo is optional and intentionally not auto-downloaded. Musubi trains on RAW.

## Template
Image after build: `ghcr.io/lokitsar/h3-musubi-runpod:v1.0.2`

Ports:
- 8677 HTTP Musubi
- 8888 HTTP Jupyter
- 22 TCP SSH

Persistent storage: 150 GB at `/workspace`

Environment:
- `MUSUBI_USER=musubi`
- `MUSUBI_PASSWORD=<secret>`
- `JUPYTER_PASSWORD=<secret>`
- `PUBLIC_KEY=<your SSH public key>`
- `HF_TOKEN=<secret>` only required for Krea 2

Leave Start command blank.
