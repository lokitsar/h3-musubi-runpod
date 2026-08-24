#!/usr/bin/env bash
set -euo pipefail

MUSUBI_HOME="${MUSUBI_HOME:-/opt/musubi}"
WORKSPACE="/workspace"
MUSUBI_PORT="${MUSUBI_PORT:-8676}"
PUBLIC_PORT="${MUSUBI_PUBLIC_PORT:-8677}"
MUSUBI_USER="${MUSUBI_USER:-musubi}"

mkdir -p \
  "${WORKSPACE}/datasets" \
  "${WORKSPACE}/models" \
  "${WORKSPACE}/output" \
  "${WORKSPACE}/cache" \
  "${WORKSPACE}/logs" \
  "${WORKSPACE}/projects" \
  /run/sshd

if [[ -n "${PUBLIC_KEY:-}" ]]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  touch /root/.ssh/authorized_keys
  grep -qxF "${PUBLIC_KEY}" /root/.ssh/authorized_keys || echo "${PUBLIC_KEY}" >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

/usr/sbin/sshd || true

if [[ -z "${MUSUBI_PASSWORD:-}" && -s "${WORKSPACE}/MUSUBI_LOGIN.txt" ]]; then
  MUSUBI_PASSWORD="$(awk -F': ' '/^Password:/ {print $2}' "${WORKSPACE}/MUSUBI_LOGIN.txt" | head -n1)"
fi

if [[ -z "${MUSUBI_PASSWORD:-}" ]]; then
  MUSUBI_PASSWORD="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(18))
PY
)"
fi

htpasswd -bc /etc/nginx/.musubi_htpasswd "${MUSUBI_USER}" "${MUSUBI_PASSWORD}" >/dev/null 2>&1

cat > "${WORKSPACE}/MUSUBI_LOGIN.txt" <<EOF
Musubi URL: use RunPod's HTTP Connect link for port ${PUBLIC_PORT}
Username: ${MUSUBI_USER}
Password: ${MUSUBI_PASSWORD}
EOF
chmod 600 "${WORKSPACE}/MUSUBI_LOGIN.txt"

cat > /etc/nginx/sites-available/default <<EOF
server {
    listen ${PUBLIC_PORT};
    server_name _;
    client_max_body_size 100m;

    auth_basic "H3 Musubi";
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
EOF

nginx

cd "${MUSUBI_HOME}"
nohup "${MUSUBI_HOME}/venv/bin/python" -m modern_gui.server \
  --no-browser --host 127.0.0.1 --port "${MUSUBI_PORT}" \
  > "${WORKSPACE}/logs/musubi.log" 2>&1 &

echo "Waiting for Musubi..."
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${MUSUBI_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${MUSUBI_PORT}/api/health" >/dev/null 2>&1; then
  echo "Musubi failed to become healthy. Last log lines:"
  tail -n 100 "${WORKSPACE}/logs/musubi.log" || true
else
  echo "Musubi is ready behind authenticated HTTP port ${PUBLIC_PORT}."
  echo "Credentials: ${WORKSPACE}/MUSUBI_LOGIN.txt"
fi

if [[ "${DISABLE_JUPYTER:-0}" != "1" ]]; then
  JUPYTER_TOKEN="${JUPYTER_PASSWORD:-}"
  if [[ -z "${JUPYTER_TOKEN}" ]]; then
    JUPYTER_TOKEN="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(18))
PY
)"
    echo "Jupyter token: ${JUPYTER_TOKEN}" > "${WORKSPACE}/JUPYTER_LOGIN.txt"
    chmod 600 "${WORKSPACE}/JUPYTER_LOGIN.txt"
  fi

  nohup jupyter lab \
    --allow-root \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --ServerApp.root_dir="${WORKSPACE}" \
    --IdentityProvider.token="${JUPYTER_TOKEN}" \
    > "${WORKSPACE}/logs/jupyter.log" 2>&1 &
fi

while true; do
  if ! pgrep -f "modern_gui.server.*${MUSUBI_PORT}" >/dev/null; then
    echo "Musubi process exited."
    tail -n 100 "${WORKSPACE}/logs/musubi.log" || true
    exit 1
  fi
  sleep 30
done
