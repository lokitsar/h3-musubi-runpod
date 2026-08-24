# v1.0.3 upgrade notes

This is a convenience-layer upgrade. It does not change the H3 or Krea2 trainer implementation.

Replace/copy these files into the repository root:

- Dockerfile
- .github/workflows/build.yml
- docker/patch_remote_ui.py
- docker/patch_runpod_workflow.py
- docker/runpod_datasets.py
- docker/post_start.sh
- README.md
- UPGRADE_NOTES.md

Keep the existing v1.0.2 model-manager files as supplied in this package.

GitHub Actions builds:

`ghcr.io/lokitsar/h3-musubi-runpod:v1.0.3`

Then change the RunPod template Container image to that tag. Do not add AUTO_DOWNLOAD_H3_MODELS.

The normal v1.0.3 dataset flow is now:

Jupyter upload -> /workspace/datasets/<name> -> New training -> Dataset -> Use dataset -> train.
