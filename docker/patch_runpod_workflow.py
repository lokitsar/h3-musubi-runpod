#!/usr/bin/env python3
from pathlib import Path
import sys

server_path = Path(sys.argv[1])
app_path = Path(sys.argv[2])
index_path = Path(sys.argv[3])

server = server_path.read_text(encoding="utf-8")
app = app_path.read_text(encoding="utf-8")
index = index_path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Could not patch {label}: expected source marker was not found.")
    return text.replace(old, new, 1)


# ---------------- server.py ----------------
server = replace_once(
    server,
    "from modern_gui.runpod_models import bundle_status, ensure_bundle\n",
    "from modern_gui.runpod_models import bundle_status, ensure_bundle\nfrom modern_gui.runpod_datasets import scan_datasets as scan_runpod_datasets, use_dataset as use_runpod_dataset\n",
    "RunPod dataset import",
)
server = replace_once(
    server,
    '        "/api/models/ensure",\n',
    '        "/api/models/ensure",\n        "/api/runpod/dataset/use",\n',
    "RunPod dataset write permission",
)
server = replace_once(
    server,
    '            if parsed.path == "/api/models/status":\n',
    '            if parsed.path == "/api/runpod/datasets":\n                return self._json(scan_runpod_datasets())\n            if parsed.path == "/api/models/status":\n',
    "RunPod dataset scan route",
)
server = replace_once(
    server,
    '            if self.path == "/api/models/ensure":\n',
    '            if self.path == "/api/runpod/dataset/use":\n                result = use_runpod_dataset(str(body.get("path") or ""))\n                settings = load_settings()\n                settings["dataset_config"] = result["toml_path"]\n                save_settings(settings)\n                return self._json({**result, "document": load_document(result["toml_path"])})\n            if self.path == "/api/models/ensure":\n',
    "RunPod dataset use route",
)

# ---------------- app.js ----------------
app = replace_once(
    app,
    "let loadedFaceResult = null;\n",
    "let loadedFaceResult = null;\nlet runpodDatasetsCache = [];\n",
    "RunPod dataset client cache",
)

old_dirty = '''function setDatasetDirty(dirty = true) {
  state.datasetDirty = dirty;
  const save=$("#save-dataset"),status=$("#dataset-document-state");
  if(save)save.disabled=!state.dataset||(!state.datasetDirty&&!state.datasetFormDirty&&!state.datasetRawDirty);
  if(status){
    status.textContent=!state.dataset?"Not loaded":(state.datasetRawDirty?"TOML needs parsing":state.datasetFormDirty?"Updating draft…":state.datasetDirty?"Unsaved changes":"Saved");
    status.classList.toggle("dirty",!!state.dataset&&(state.datasetDirty||state.datasetFormDirty||state.datasetRawDirty));
  }
  updateSaveState();
}'''
new_dirty = '''function setDatasetDirty(dirty = true) {
  state.datasetDirty = dirty;
  const save=$("#save-dataset"),status=$("#dataset-document-state"),pathInput=$("#dataset-path");
  const pathChanged=!!state.dataset&&!!pathInput?.value.trim()&&!sameLocalPath(state.dataset.path,pathInput.value);
  if(save)save.disabled=!state.dataset||(!state.datasetDirty&&!state.datasetFormDirty&&!state.datasetRawDirty&&!pathChanged);
  if(status){
    status.textContent=!state.dataset?"Not loaded":(state.datasetRawDirty?"TOML needs parsing":state.datasetFormDirty?"Updating draft...":state.datasetDirty?"Unsaved changes":pathChanged?"New save path":"Saved");
    status.classList.toggle("dirty",!!state.dataset&&(state.datasetDirty||state.datasetFormDirty||state.datasetRawDirty||pathChanged));
  }
  updateSaveState();
}'''
app = replace_once(app, old_dirty, new_dirty, "Save TOML path-change behavior")

quick_js = r'''
function runpodDatasetLabel(item) {
  const media = `${item.media_count} ${item.kind}${item.media_count===1?"":"s"}`;
  const captions = item.caption_count ? `${item.caption_coverage}% captions` : "no sidecar captions";
  return `${item.name} · ${media} · ${captions}`;
}

function renderRunpodDatasetPickers() {
  const select=$("#runpod-dataset-select");
  if(select){
    const previous=select.value;
    select.innerHTML=runpodDatasetsCache.length
      ? runpodDatasetsCache.map(item=>`<option value="${esc(item.path)}">${esc(runpodDatasetLabel(item))}</option>`).join("")
      : '<option value="">No datasets found in /workspace/datasets</option>';
    if(previous&&runpodDatasetsCache.some(item=>item.path===previous))select.value=previous;
    $("#use-runpod-dataset").disabled=!runpodDatasetsCache.length;
    const hint=$("#runpod-dataset-hint");
    if(hint)hint.textContent=runpodDatasetsCache.length
      ? "Use dataset creates or reuses a TOML in /workspace/projects and selects it for this training recipe."
      : "Upload a folder of images and matching .txt captions to /workspace/datasets in Jupyter, then refresh.";
  }

  const list=$("#runpod-dataset-list");
  if(list){
    list.innerHTML="";
    if(!runpodDatasetsCache.length){
      list.innerHTML='<div class="empty">No media folders found yet. Upload a dataset under /workspace/datasets, then refresh.</div>';
    }else{
      runpodDatasetsCache.forEach(item=>{
        const button=document.createElement("button");
        button.type="button";
        button.className="workspace-link";
        button.innerHTML=`<span>▦</span><span><strong>${esc(item.name)}</strong><small>${esc(runpodDatasetLabel(item))}${item.toml_exists?" · TOML ready":""}</small></span><b>Use →</b>`;
        button.addEventListener("click",()=>useRunpodDataset(item.path,button));
        list.append(button);
      });
    }
  }
}

async function loadRunpodDatasets({quiet=false}={}) {
  const payload=await api("/api/runpod/datasets");
  runpodDatasetsCache=payload.datasets||[];
  renderRunpodDatasetPickers();
  if(!quiet&&!runpodDatasetsCache.length)toast("No datasets found under /workspace/datasets yet.");
  return runpodDatasetsCache;
}

async function useRunpodDataset(path, button=null) {
  const task=async()=>{
    const payload=await api("/api/runpod/dataset/use",{method:"POST",body:JSON.stringify({path})});
    state.settings.dataset_config=payload.toml_path;
    if(payload.document)renderDataset(payload.document,0);
    setDatasetDirty(false);
    renderGuided();renderAllSettings();sync(false);
    await loadRunpodDatasets({quiet:true});
    toast(`${payload.name} is ready for training${payload.created?"; TOML created":"; existing TOML selected"}.`,"success");
    return payload;
  };
  return button?withBusy(button,"Preparing...",task):task();
}

'''
app = replace_once(app, "function renderGuided() {\n", quick_js + "function renderGuided() {\n", "RunPod dataset UI functions")
app = replace_once(
    app,
    '  if (view === "datasets") ensureDatasetLoaded();\n',
    '  if (view === "datasets") { ensureDatasetLoaded(); loadRunpodDatasets({quiet:true}).catch(e=>toast(e.message,"error")); }\n',
    "RunPod dataset scan on workspace open",
)
app = replace_once(
    app,
    'function setStep(step) {\n  state.step = step;\n',
    'function setStep(step) {\n  state.step = step;\n  if(step==="data")loadRunpodDatasets({quiet:true}).catch(e=>toast(e.message,"error"));\n',
    "RunPod dataset scan on data step",
)
app = replace_once(
    app,
    '$("#dataset-path").addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();loadDatasetDocument()}});\n',
    '$("#dataset-path").addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();loadDatasetDocument()}});\n$("#dataset-path").addEventListener("input",()=>setDatasetDirty(state.datasetDirty));\n',
    "Save TOML input watcher",
)
app = replace_once(
    app,
    '$("#load-dataset").addEventListener("click",()=>loadDatasetDocument());\n',
    '$("#load-dataset").addEventListener("click",()=>loadDatasetDocument());\n$("#refresh-runpod-datasets")?.addEventListener("click",event=>withBusy(event.currentTarget,"Refreshing...",()=>loadRunpodDatasets({quiet:true})).catch(e=>toast(e.message,"error")));\n$("#refresh-runpod-datasets-setup")?.addEventListener("click",event=>withBusy(event.currentTarget,"Refreshing...",()=>loadRunpodDatasets({quiet:true})).catch(e=>toast(e.message,"error")));\n$("#use-runpod-dataset")?.addEventListener("click",event=>{const path=$("#runpod-dataset-select")?.value;if(path)useRunpodDataset(path,event.currentTarget).catch(e=>toast(e.message,"error"));});\n',
    "RunPod dataset controls",
)
app = replace_once(
    app,
    '$("#run-accelerate-config").addEventListener("click",()=>api("/api/tools/accelerate-config",{method:"POST",body:"{}"}).then(()=>toast("Accelerate terminal opened.")).catch(e=>toast(e.message)));\n',
    '$("#run-accelerate-config")?.addEventListener("click",()=>api("/api/tools/accelerate-config",{method:"POST",body:"{}"}).then(()=>toast("Accelerate terminal opened.")).catch(e=>toast(e.message)));\n',
    "optional Accelerate tool",
)

# ---------------- index.html ----------------
index = replace_once(
    index,
    '<div id="data-fields" class="guided-fields"></div>\n',
    '<div id="data-fields" class="guided-fields"></div>\n'
    '              <section class="plan-policy-card" id="runpod-dataset-picker"><div><strong>RunPod quick dataset</strong><p>Choose a media folder already uploaded under /workspace/datasets. Musubi will create or reuse its TOML and select it automatically.</p></div><div class="path-bar"><label for="runpod-dataset-select">Dataset folder</label><select id="runpod-dataset-select"><option>Scanning /workspace/datasets...</option></select><button class="primary" id="use-runpod-dataset">Use dataset</button><button class="quiet" id="refresh-runpod-datasets-setup">Refresh</button></div><small id="runpod-dataset-hint">Upload datasets with Jupyter, then choose one here.</small></section>\n',
    "RunPod quick picker in training recipe",
)
index = replace_once(
    index,
    '        <div class="path-bar dataset-path-bar"><label for="dataset-path">Dataset TOML</label>',
    '        <section class="activity-panel" id="runpod-dataset-card"><div class="section-title"><div><p class="kicker">RUNPOD QUICK START</p><h2>Datasets in /workspace/datasets</h2><p>Pick a folder and Musubi creates or reuses its TOML automatically.</p></div><button class="quiet" id="refresh-runpod-datasets">Refresh folders</button></div><div id="runpod-dataset-list" class="dataset-list empty">Scanning /workspace/datasets...</div></section>\n        <div class="path-bar dataset-path-bar"><label for="dataset-path">Dataset TOML</label>',
    "RunPod quick picker in dataset workspace",
)
old_tool = '<article class="tool-panel"><p class="kicker">ONE-TIME SETUP</p><h2>Configure Accelerate</h2><p>Opens an interactive terminal for the Accelerate configuration used by Musubi.</p><ul><li>This machine</li><li>No distributed training</li><li>GPU training</li><li>No DeepSpeed</li><li>BF16 or FP16 precision</li></ul><button class="primary" id="run-accelerate-config">Open Accelerate config</button></article>'
new_tool = '<article class="tool-panel"><p class="kicker">RUNPOD TEMPLATE</p><h2>Environment ready</h2><p>Accelerate, CUDA, torchvision, Jupyter, SSH, and the Musubi launch environment are preconfigured by this template. No one-time setup is required for normal single-GPU training.</p><ul><li>Use Convert LoRA only when you need a format change</li><li>Model bundles are managed from the Model step</li><li>Datasets live under /workspace/datasets</li><li>Outputs live under /workspace/output</li></ul></article>'
index = replace_once(index, old_tool, new_tool, "RunPod-ready Tools panel")

server_path.write_text(server, encoding="utf-8")
app_path.write_text(app, encoding="utf-8")
index_path.write_text(index, encoding="utf-8")
print(f"Patched RunPod dataset workflow in {server_path}, {app_path}, and {index_path}")
