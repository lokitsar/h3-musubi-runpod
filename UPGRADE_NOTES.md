# v1.0.1 upgrade notes

This package is a drop-in replacement for the files in the `lokitsar/h3-musubi-runpod` repository.

The key design change is that the Docker image NO LONGER overrides the RunPod base image CMD. RunPod's official `/start.sh` now owns SSH and Jupyter. Musubi is started through `/post_start.sh`.

Files to replace/add:
- Replace `Dockerfile`
- Replace `.github/workflows/build.yml`
- Replace `docker/patch_remote_ui.py`
- Add `docker/patch_linux_defaults.py`
- Add `docker/post_start.sh`
- Add `docker/download_h3_models.sh`
- README.md is optional but recommended

`docker/start.sh` from v1.0.0 can remain in the repository; v1.0.1 no longer copies or uses it.

After committing, GitHub Actions should build:
- `ghcr.io/lokitsar/h3-musubi-runpod:v1.0.1`
- `ghcr.io/lokitsar/h3-musubi-runpod:latest`

Then edit the RunPod template image from `:v1.0.0` to `:v1.0.1`.
