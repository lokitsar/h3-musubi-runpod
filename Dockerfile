FROM runpod/pytorch:1.0.3-cu1300-torch291-ubuntu2404

ARG DEBIAN_FRONTEND=noninteractive
ARG MUSUBI_COMMIT=ee845c7659ff7a505c905388310cdf488460184e

ENV MUSUBI_HOME=/opt/musubi \
    MUSUBI_CUDA=cu130 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/opt/musubi/venv/bin:${PATH} \
    HF_HOME=/workspace/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates ffmpeg apache2-utils rsync \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /workspace

RUN git clone https://github.com/diodiogod/musubi-tuner_simple_GUI.git "${MUSUBI_HOME}" \
    && cd "${MUSUBI_HOME}" \
    && git checkout "${MUSUBI_COMMIT}" \
    && python -m venv --system-site-packages "${MUSUBI_HOME}/venv" \
    && "${MUSUBI_HOME}/venv/bin/python" -m pip install --no-cache-dir --upgrade pip \
    && "${MUSUBI_HOME}/venv/bin/python" -m pip install --no-cache-dir -e . \
    && "${MUSUBI_HOME}/venv/bin/python" -m pip install --no-cache-dir --no-deps \
         --index-url https://download.pytorch.org/whl/cu130 \
         torchvision==0.24.1 \
    && ln -sf "${MUSUBI_HOME}/venv/bin/accelerate" /usr/local/bin/accelerate \
    && "${MUSUBI_HOME}/venv/bin/python" - <<'PY'
import accelerate
import torch
import torchvision
print("torch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("accelerate:", accelerate.__version__)
PY

COPY docker/patch_remote_ui.py /tmp/patch_remote_ui.py
RUN python /tmp/patch_remote_ui.py "${MUSUBI_HOME}/modern_gui/static/app.js" \
    && rm /tmp/patch_remote_ui.py

COPY docker/patch_linux_defaults.py /tmp/patch_linux_defaults.py
RUN python /tmp/patch_linux_defaults.py "${MUSUBI_HOME}/Base_SETTINGS.json" \
    && rm /tmp/patch_linux_defaults.py

COPY docker/runpod_models.py "${MUSUBI_HOME}/modern_gui/runpod_models.py"
COPY docker/patch_model_bundles.py /tmp/patch_model_bundles.py
RUN python /tmp/patch_model_bundles.py \
      "${MUSUBI_HOME}/modern_gui/server.py" \
      "${MUSUBI_HOME}/modern_gui/static/app.js" \
    && rm /tmp/patch_model_bundles.py

COPY docker/runpod_datasets.py "${MUSUBI_HOME}/modern_gui/runpod_datasets.py"
COPY docker/patch_runpod_workflow.py /tmp/patch_runpod_workflow.py
RUN python /tmp/patch_runpod_workflow.py \
      "${MUSUBI_HOME}/modern_gui/server.py" \
      "${MUSUBI_HOME}/modern_gui/static/app.js" \
      "${MUSUBI_HOME}/modern_gui/static/index.html" \
    && rm /tmp/patch_runpod_workflow.py

COPY docker/musubi-models /usr/local/bin/musubi-models
COPY docker/post_start.sh /post_start.sh
RUN chmod +x /post_start.sh /usr/local/bin/musubi-models

EXPOSE 22 8677 8888
WORKDIR /workspace

# Intentionally inherit RunPod's native /start.sh CMD.
