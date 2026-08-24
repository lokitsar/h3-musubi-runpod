#!/usr/bin/env python3
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

defaults = {
    "training_mode": "MiniMax H3 (Experimental)",
    "dataset_config": "",
    "project_root": "/workspace/projects",
    "output_dir": "/workspace/output",
    "output_name": "lora",
    "starting_point_mode": "new",

    "minimax_h3_training_workflow": "Still images · compact ConvRot",
    "minimax_h3_dit_model": "/workspace/models/h3/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "minimax_h3_text_encoder": "/workspace/models/h3/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "minimax_h3_tokenizer": "MiniMaxAI/MiniMax-H3",
    "minimax_h3_convrot_bwd_mode": "bf16",
    "minimax_h3_text_encoder_blocks_to_swap": "50",
    "minimax_h3_text_cache_dtype": "bfloat16",

    "krea2_dit_model": "/workspace/models/krea2/raw.safetensors",
    "krea2_text_encoder": "/workspace/models/krea2/text_encoders/qwen3vl_4b_bf16.safetensors",
    "krea2_turbo_dit": "",
    "krea2_projector_diff": "",

    "vae_model": "/workspace/models/h3/vae/minimax_h3_video_vae_fp16.safetensors",
    "network_type": "LoRA",
    "network_dim_low": "16",
    "network_alpha_low": "16",
    "learning_rate": "1e-4",
    "optimizer_type": "adamw8bit",
    "optimizer_args": "weight_decay=0.1",
    "lr_scheduler": "cosine",
    "lr_warmup_steps": "0",
    "lr_scheduler_num_cycles": "1",
    "lr_scheduler_min_lr_ratio": "5e-5",
    "max_train_epochs": "20",
    "save_every_n_epochs": "2",
    "save_every_n_steps": "",
    "seed": "42",
    "mixed_precision": "bf16",
    "gradient_checkpointing": True,
    "persistent_data_loader_workers": True,
    "max_data_loader_n_workers": "2",
    "gradient_accumulation_steps": "1",
    "blocks_to_swap": "30",
    "attention_mechanism": "sdpa",
    "fp8_base": False,
    "fp8_scaled": False,
    "timestep_sampling": "krea2_shift",
    "num_timestep_buckets": "2",
    "discrete_flow_shift": "1.0",
    "preserve_distribution_shape": True,
    "recache_latents": True,
    "recache_text": True,

    "minimax_h3_quality_protection_method": "Dynamic Sigma (recommended)",
    "minimax_h3_quality_protection_preset": "Proven Quality",
    "minimax_h3_training_assistant_enabled": False,
    "minimax_h3_dynamic_sigma_enabled": True,
    "minimax_h3_dynamic_sigma_every_n_steps": "1",
    "minimax_h3_guidance_distillation_protection": True,
    "minimax_h3_guidance_distillation_scale": "4.0",
    "minimax_h3_guidance_distillation_schedule": "sigma",
    "minimax_h3_guidance_distillation_sigma_min": "0.15",
    "minimax_h3_base_preservation_enabled": False,
}

for key in [
    "dit_high_noise", "dit_low_noise", "t5_model", "clip_model",
    "logging_dir", "resume_path", "network_weights",
    "convert_lora_path", "convert_output_dir",
]:
    if key in data:
        data[key] = ""

data.update(defaults)
path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Patched RunPod/Linux defaults in {path}")
