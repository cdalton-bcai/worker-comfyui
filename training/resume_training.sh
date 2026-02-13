#!/bin/bash
echo "Resuming training from epoch 6..."
echo "Running in background with nohup to prevent timeout."
echo "Logs will be written to /workspace/training_log.txt"
cd /workspace/sd-scripts

nohup accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py \
  --pretrained_model_name_or_path="/workspace/models/lustifySDXLNSFW_ggwpV7.safetensors" \
  --vae="/workspace/models/sdxl-vae-fp16-fix.safetensors" \
  --dataset_config="/workspace/dataset_config.toml" \
  --output_dir="/workspace/output" \
  --output_name="winter_girl_lora_v2" \
  --save_model_as="safetensors" \
  --save_precision="fp16" \
  --save_every_n_epochs=1 \
  --max_train_epochs=16 \
  --seed=42 \
  --gradient_checkpointing \
  --mixed_precision="bf16" \
  --optimizer_type="AdamW8bit" \
  --learning_rate=1e-4 \
  --lr_scheduler="cosine" \
  --lr_warmup_steps=50 \
  --xformers \
  --cache_latents \
  --cache_latents_to_disk \
  --cache_text_encoder_outputs \
  --network_module="networks.lora" \
  --network_dim=32 \
  --network_alpha=16 \
  --network_train_unet_only \
  --logging_dir="/workspace/logs" \
  --network_weights="/workspace/output/winter_girl_lora-000006.safetensors" > /workspace/training_log.txt 2>&1 &

echo "Training started in background."
echo "To check progress, run: tail -f /workspace/training_log.txt"
