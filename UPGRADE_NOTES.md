# v1.0.2 upgrade

Copy this package over the repository root and commit it.
Delete the old `docker/download_h3_models.sh` if it still exists.

GitHub Actions builds:
`ghcr.io/lokitsar/h3-musubi-runpod:v1.0.2`

Then change the RunPod template Container image to that tag.
Do not add AUTO_DOWNLOAD_H3_MODELS.
For Krea 2, add HF_TOKEN as a RunPod secret.
