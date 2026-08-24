#!/usr/bin/env bash
set -euo pipefail

MUSUBI_HOME="${MUSUBI_HOME:-/opt/musubi}"
WORKSPACE="${RP_WORKSPACE:-/workspace}"
MUSUBI_PORT="${MUSUBI_PORT:-8676}"
PUBLIC_PORT="${MUSUBI_PUBLIC_PORT:-8677}"
MUSUBI_USER="${MUSUBI_USER:-musubi}"

mkdir -p \
  "${WORKSPACE}/datasets" \
  "${WORKSPACE}/models/h3" \
  "${WORKSPACE}/models/krea2" \
  "${WORKSPACE}/output" \
  "${WORKSPACE}/cache" \
  "${WORKSPACE}/logs" \
  "${WORKSPACE}/projects" \
  "${WORKSPACE}/.cache/huggingface"

GENERATED_PASSWORD=0
if [[ -z "${MUSUBI_PASSWORD:-}" && -s "${WORKSPACE}/MUSUBI_LOGIN.txt" ]]; then
  MUSUBI_PASSWORD="$(awk -F': ' '/^Password:/ {print $2}' "${WORKSPACE}/MUSUBI_LOGIN.txt" | head -n1)"
fi
if [[ -z "${MUSUBI_PASSWORD:-}" ]]; then
  GENERATED_PASSWORD=1
  MUSUBI_PASSWORD="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(18))
PY
)"
fi

htpasswd -bc /etc/nginx/.musubi_htpasswd "${MUSUBI_USER}" "${MUSUBI_PASSWORD}" >/dev/null 2>&1
{
  echo "Musubi URL: use RunPod HTTP Connect for port ${PUBLIC_PORT}"
  echo "Username: ${MUSUBI_USER}"
  if [[ "${GENERATED_PASSWORD}" == "1" ]]; then
    echo "Password: ${MUSUBI_PASSWORD}"
  else
    echo "Password: supplied by MUSUBI_PASSWORD RunPod secret"
  fi
} > "${WORKSPACE}/MUSUBI_LOGIN.txt"
chmod 600 "${WORKSPACE}/MUSUBI_LOGIN.txt"

cat > /etc/nginx/musubi-standalone.conf <<EOF2
pid /run/musubi-nginx.pid;
error_log ${WORKSPACE}/logs/musubi-nginx-error.log;
events {}
http {
    access_log ${WORKSPACE}/logs/musubi-nginx-access.log;
    server {
        listen 0.0.0.0:${PUBLIC_PORT};
        server_name _;
        client_max_body_size 2g;
        auth_basic "Musubi";
        auth_basic_user_file /etc/nginx/.musubi_htpasswd;
        location / {
            proxy_pass http://127.0.0.1:${MUSUBI_PORT};
            proxy_http_version 1.1;
            proxy_set_header Host 127.0.0.1:${MUSUBI_PORT};
            proxy_set_header Origin http://127.0.0.1:${MUSUBI_PORT};
            proxy_set_header X-Forwarded-For \$remote_addr;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_buffering off;
            proxy_read_timeout 3600;
            proxy_send_timeout 3600;
        }
    }
}
EOF2

nginx -t -c /etc/nginx/musubi-standalone.conf
nginx -c /etc/nginx/musubi-standalone.conf

cd "${MUSUBI_HOME}"
nohup env PATH="${MUSUBI_HOME}/venv/bin:${PATH}" \
  "${MUSUBI_HOME}/venv/bin/python" -m modern_gui.server \
  --no-browser --host 127.0.0.1 --port "${MUSUBI_PORT}" \
  > "${WORKSPACE}/logs/musubi.log" 2>&1 &

READY=0
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${MUSUBI_PORT}/api/health" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
if [[ "${READY}" != "1" ]]; then
  tail -n 100 "${WORKSPACE}/logs/musubi.log" || true
  exit 1
fi
if ! curl -fsS -u "${MUSUBI_USER}:${MUSUBI_PASSWORD}" "http://127.0.0.1:${PUBLIC_PORT}/api/health" >/dev/null 2>&1; then
  tail -n 100 "${WORKSPACE}/logs/musubi-nginx-error.log" || true
  exit 1
fi

echo "[Musubi] Ready on RunPod HTTP port ${PUBLIC_PORT}."
echo "[Musubi] Jupyter/SSH are handled by RunPod's native startup."

cat > "${WORKSPACE}/MUSUBI_RUNPOD_README.txt" <<'EOF3'
Musubi RunPod quick paths
Datasets:      /workspace/datasets
Dataset TOMLs: /workspace/projects
Models:        /workspace/models
LoRA outputs:  /workspace/output
Logs:          /workspace/logs

Model behavior:
- Select MiniMax H3: Musubi offers to download missing H3 files.
- Select Krea 2: Musubi offers to download missing Krea2 training files.
- Nothing large downloads at pod startup.
- Krea-2 Raw requires HF_TOKEN and Hugging Face access to krea/Krea-2-Raw.
- Krea-2 Turbo is optional and is not downloaded automatically.
EOF3
