#!/bin/bash

# Write dataset config (separate file)
cat > /workspace/dataset_config.toml << 'DATASET'
[general]
enable_bucket = true

[[datasets]]
resolution = 1024
batch_size = 1
min_bucket_reso = 512
max_bucket_reso = 2048
bucket_reso_steps = 64

  [[datasets.subsets]]
  image_dir = "/workspace/dataset/27_winter_girl"
  caption_extension = ".txt"
  num_repeats = 27
DATASET

echo "Dataset config written."
echo "Images in dataset folder:"
ls /workspace/dataset/27_winter_girl/*.png | head -5
echo "..."
ls /workspace/dataset/27_winter_girl/*.png | wc -l
echo "total images"

echo "Launching training..."
cd /workspace/sd-scripts

accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py \
  --pretrained_model_name_or_path="/workspace/models/lustifySDXLNSFW_ggwpV7.safetensors" \
  --vae="/workspace/models/sdxl-vae-fp16-fix.safetensors" \
  --dataset_config="/workspace/dataset_config.toml" \
  --output_dir="/workspace/output" \
  --output_name="winter_girl_lora" \
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
  --logging_dir="/workspace/logs"
