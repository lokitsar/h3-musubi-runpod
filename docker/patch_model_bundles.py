#!/usr/bin/env python3
from pathlib import Path
import sys

server_path = Path(sys.argv[1])
app_path = Path(sys.argv[2])
server = server_path.read_text(encoding="utf-8")
app = app_path.read_text(encoding="utf-8")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Could not patch {label}: expected source marker was not found.")
    return text.replace(old, new, 1)

server = replace_once(
    server,
    "from modern_gui.settings import load_settings, save_settings, settings_schema\n",
    "from modern_gui.settings import load_settings, save_settings, settings_schema\nfrom modern_gui.runpod_models import bundle_status, ensure_bundle\n",
    "server import",
)
server = replace_once(
    server,
    '        "/api/settings",\n',
    '        "/api/settings",\n        "/api/models/ensure",\n',
    "model ensure local-action registration",
)
server = replace_once(
    server,
    '            if parsed.path == "/api/settings":\n                settings = load_settings()\n                return self._json({"settings": settings, "schema": settings_schema(settings)})\n',
    '            if parsed.path == "/api/models/status":\n                mode = parse_qs(parsed.query).get("mode", [""])[0]\n                return self._json(bundle_status(mode))\n            if parsed.path == "/api/settings":\n                settings = load_settings()\n                return self._json({"settings": settings, "schema": settings_schema(settings)})\n',
    "model status route",
)
server = replace_once(
    server,
    '            body = self._body()\n            if self.path == "/api/settings":\n                return self._json({"settings": save_settings(body.get("settings", {}))})\n',
    '            body = self._body()\n            if self.path == "/api/models/ensure":\n                result = ensure_bundle(str(body.get("mode") or ""))\n                settings = load_settings()\n                settings.update(result.get("settings_patch") or {})\n                save_settings(settings)\n                return self._json(result)\n            if self.path == "/api/settings":\n                return self._json({"settings": save_settings(body.get("settings", {}))})\n',
    "model ensure route",
)

app = replace_once(
    app,
    'depthGpuSnapshot: null };',
    'depthGpuSnapshot: null, modelBundle: {mode:"", ready:false, checking:false, downloading:false, missing:[]} };',
    "model bundle client state",
)

bundle_js = r'''
function bundleModeSupported(mode) {
  return mode === "Krea 2" || mode === "MiniMax H3 (Experimental)";
}

function renderModelBundleNotice(mode) {
  const host = $("#model-fields");
  if (!host) return;
  host.querySelector(".runpod-model-bundle")?.remove();
  if (!bundleModeSupported(mode)) return;
  const status = state.modelBundle || {};
  if (status.mode !== mode) return;
  const box = document.createElement("div");
  box.className = `runpod-model-bundle ${status.ready ? "continuation-note new" : "issue warning"}`;
  if (status.checking) {
    box.innerHTML = `<strong>Checking ${esc(mode)} models...</strong>`;
  } else if (status.downloading) {
    box.innerHTML = `<strong>Downloading ${esc(status.label || mode)} models...</strong><span>Keep this pod running. Files are being saved under /workspace/models and will be reused later.</span>`;
  } else if (status.error) {
    box.innerHTML = `<strong>Model setup needs attention</strong><span>${esc(status.error)}</span>`;
  } else if (status.ready) {
    box.innerHTML = `<strong>${esc(status.label || mode)} models ready</strong><span>Required files are already present in /workspace/models.</span>`;
  } else {
    const tokenNote = status.requires_hf_token
      ? `<span>Krea-2 Raw is gated. Add <code>HF_TOKEN</code> as a RunPod secret and grant that Hugging Face account access to krea/Krea-2-Raw.</span>`
      : "";
    box.innerHTML = `<strong>${esc(status.label || mode)} models are not installed</strong><span>Required download: ${esc(status.size_note || "model bundle")}.</span>${tokenNote}`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "quiet";
    button.textContent = `Download ${status.label || mode} models`;
    button.addEventListener("click", () => downloadModelBundle(mode));
    box.append(button);
  }
  host.prepend(box);
}

async function refreshModelBundle(mode, offerDownload = false) {
  if (!bundleModeSupported(mode)) return;
  try {
    const result = await api(`/api/models/status?mode=${encodeURIComponent(mode)}`);
    state.modelBundle = {...result, checking:false, downloading:false};
    if (result.settings_patch) Object.assign(state.settings, result.settings_patch);
    renderModelBundleNotice(mode);
    if (offerDownload && !result.ready) {
      const gated = result.requires_hf_token ? "\n\nKrea-2 Raw is gated and requires HF_TOKEN in the RunPod template." : "";
      if (confirm(`${result.label} needs ${result.size_note} of model files. Download the missing files now?${gated}`)) {
        downloadModelBundle(mode);
      }
    }
  } catch (e) {
    state.modelBundle = {mode, ready:false, checking:false, downloading:false, missing:[], error:e.message};
    renderModelBundleNotice(mode);
    toast(e.message, "error");
  }
}

async function downloadModelBundle(mode) {
  if (!bundleModeSupported(mode) || state.modelBundle?.downloading) return;
  state.modelBundle = {...state.modelBundle, mode, checking:false, downloading:true, error:""};
  renderModelBundleNotice(mode);
  toast(`Downloading ${state.modelBundle.label || mode} models...`);
  try {
    const result = await api("/api/models/ensure", {method:"POST", body:JSON.stringify({mode})});
    state.modelBundle = {...result, checking:false, downloading:false};
    if (result.settings_patch) Object.assign(state.settings, result.settings_patch);
    renderGuided();
    renderAllSettings();
    sync();
    toast(`${result.label} models are ready.`, "success");
  } catch (e) {
    state.modelBundle = {...state.modelBundle, mode, checking:false, downloading:false, error:e.message};
    renderModelBundleNotice(mode);
    toast(e.message, "error");
  }
}

'''
app = replace_once(app, "function renderGuided() {\n", bundle_js + "function renderGuided() {\n", "model bundle UI functions")
app = replace_once(
    app,
    '  appendFields($("#model-fields"), modelKeys);\n',
    '  appendFields($("#model-fields"), modelKeys);\n  renderModelBundleNotice(mode);\n  if(bundleModeSupported(mode) && state.modelBundle.mode !== mode){\n    state.modelBundle = {mode, ready:false, checking:true, downloading:false, missing:[]};\n    renderModelBundleNotice(mode);\n    refreshModelBundle(mode, false);\n  }\n',
    "model bundle card render",
)
app = replace_once(
    app,
    'function selectMode(mode) {\n  state.settings.training_mode = mode;\n  if(mode === "MiniMax H3 (Experimental)"){\n    Object.assign(state.settings, {\n',
    'function selectMode(mode) {\n  state.settings.training_mode = mode;\n  if(mode === "Krea 2"){\n    Object.assign(state.settings, {\n      krea2_dit_model:"/workspace/models/krea2/raw.safetensors",\n      krea2_text_encoder:"/workspace/models/krea2/text_encoders/qwen3vl_4b_bf16.safetensors",\n      vae_model:"/workspace/models/krea2/split_files/vae/qwen_image_vae.safetensors",\n    });\n  }\n  if(mode === "MiniMax H3 (Experimental)"){\n    Object.assign(state.settings, {\n      minimax_h3_dit_model:"/workspace/models/h3/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",\n      minimax_h3_text_encoder:"/workspace/models/h3/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",\n      vae_model:"/workspace/models/h3/vae/minimax_h3_video_vae_fp16.safetensors",\n',
    "mode-specific model paths",
)
app = replace_once(
    app,
    '  renderGuided(); renderAllSettings(); sync();\n}\nfunction setStep(step) {\n',
    '  if(bundleModeSupported(mode)) state.modelBundle = {mode, ready:false, checking:true, downloading:false, missing:[]};\n  renderGuided(); renderAllSettings(); sync();\n  if(bundleModeSupported(mode)) refreshModelBundle(mode, true);\n}\nfunction setStep(step) {\n',
    "mode selection download trigger",
)

server_path.write_text(server, encoding="utf-8")
app_path.write_text(app, encoding="utf-8")
print(f"Patched model-bundle API in {server_path}")
print(f"Patched mode-aware model setup in {app_path}")
