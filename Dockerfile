FROM runpod/pytorch:1.0.3-cu1300-torch291-ubuntu2404

ARG DEBIAN_FRONTEND=noninteractive
ARG MUSUBI_COMMIT=ee845c7659ff7a505c905388310cdf488460184e

ENV MUSUBI_HOME=/opt/musubi \
    MUSUBI_CUDA=cu130 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates ffmpeg openssh-server nginx apache2-utils rsync \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd /workspace

RUN python -m pip install --no-cache-dir --upgrade jupyterlab

RUN git clone https://github.com/diodiogod/musubi-tuner_simple_GUI.git "${MUSUBI_HOME}" \
    && cd "${MUSUBI_HOME}" \
    && git checkout "${MUSUBI_COMMIT}" \
    && python -m venv --system-site-packages "${MUSUBI_HOME}/venv" \
    && "${MUSUBI_HOME}/venv/bin/python" -m pip install --no-cache-dir --upgrade pip \
    && "${MUSUBI_HOME}/venv/bin/python" -m pip install --no-cache-dir -e .

COPY docker/patch_remote_ui.py /tmp/patch_remote_ui.py
RUN python /tmp/patch_remote_ui.py "${MUSUBI_HOME}/modern_gui/static/app.js" \
    && rm /tmp/patch_remote_ui.py

COPY docker/start.sh /usr/local/bin/h3-musubi-start
RUN chmod +x /usr/local/bin/h3-musubi-start

EXPOSE 22 8677 8888
WORKDIR /workspace
CMD ["/usr/local/bin/h3-musubi-start"]
