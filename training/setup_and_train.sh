#!/bin/bash
set -e

echo "=== Winter LoRA Training - Full Setup ==="

# ── 1. Install kohya sd-scripts ──────────────────────────────────
echo "[1/6] Installing kohya sd-scripts..."
cd /workspace
if [ ! -d "sd-scripts" ]; then
    git clone https://github.com/kohya-ss/sd-scripts.git
    cd sd-scripts
    git checkout sdxl
    pip install -r requirements.txt
    pip install bitsandbytes xformers
else
    echo "sd-scripts already installed, skipping..."
    cd sd-scripts
fi
cd /workspace

# ── 2. Download base model + VAE ─────────────────────────────────
echo "[2/6] Downloading Lustify v7 checkpoint (~6.9 GB)..."
mkdir -p /workspace/models

if [ ! -f "/workspace/models/lustifySDXLNSFW_ggwpV7.safetensors" ]; then
    wget -O /workspace/models/lustifySDXLNSFW_ggwpV7.safetensors \
        "https://huggingface.co/Kutches/XL/resolve/main/lustifySDXLNSFW_ggwpV7.safetensors"
else
    echo "Lustify v7 already downloaded, skipping..."
fi

echo "[3/6] Downloading SDXL VAE fp16 fix (~335 MB)..."
if [ ! -f "/workspace/models/sdxl-vae-fp16-fix.safetensors" ]; then
    wget -O /workspace/models/sdxl-vae-fp16-fix.safetensors \
        "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors"
else
    echo "VAE already downloaded, skipping..."
fi

# ── 3. Create training config ────────────────────────────────────
echo "[4/6] Writing training config..."
mkdir -p /workspace/output /workspace/logs

cat > /workspace/train_winter_lora.toml << 'TOML_EOF'
[sdxl_arguments]
cache_text_encoder_outputs = true

[model_arguments]
pretrained_model_name_or_path = "/workspace/models/lustifySDXLNSFW_ggwpV7.safetensors"
vae = "/workspace/models/sdxl-vae-fp16-fix.safetensors"

[dataset_arguments]
resolution = "1024,1024"
enable_bucket = true
min_bucket_reso = 512
max_bucket_reso = 2048
bucket_reso_steps = 64

[training_arguments]
output_dir = "/workspace/output"
output_name = "winter_girl_lora"
save_model_as = "safetensors"
save_precision = "fp16"
save_every_n_epochs = 1
train_batch_size = 1
max_train_epochs = 16
seed = 42
gradient_checkpointing = true
mixed_precision = "bf16"
optimizer_type = "AdamW8bit"
learning_rate = 1e-4
lr_scheduler = "cosine"
lr_warmup_steps = 50
xformers = true
cache_latents = true
cache_latents_to_disk = true
persistent_data_loader_workers = true
max_data_loader_n_workers = 2
logging_dir = "/workspace/logs"
log_prefix = "winter_girl"

[network_arguments]
network_module = "networks.lora"
network_dim = 32
network_alpha = 16
network_train_unet_only = false

[[datasets]]
[[datasets.subsets]]
image_dir = "/workspace/dataset/27_winter_girl"
caption_extension = ".txt"
num_repeats = 27
TOML_EOF

# ── 4. Wait for dataset upload ───────────────────────────────────
echo "[5/6] Checking for dataset..."
mkdir -p /workspace/dataset/27_winter_girl

if [ -d "/workspace/upload" ] && ls /workspace/upload/*.png 1>/dev/null 2>&1; then
    cp /workspace/upload/*.png /workspace/dataset/27_winter_girl/
    cp /workspace/upload/*.txt /workspace/dataset/27_winter_girl/
    IMG_COUNT=$(ls /workspace/dataset/27_winter_girl/*.png 2>/dev/null | wc -l)
    TXT_COUNT=$(ls /workspace/dataset/27_winter_girl/*.txt 2>/dev/null | wc -l)
    echo "Dataset ready: $IMG_COUNT images, $TXT_COUNT captions"
else
    echo ""
    echo "=========================================================="
    echo " DATASET NOT FOUND!"
    echo " Upload your .png and .txt files to /workspace/upload/"
    echo " Then re-run this script."
    echo "=========================================================="
    exit 1
fi

# ── 5. Launch training ───────────────────────────────────────────
echo "[6/6] Starting LoRA training..."
echo "Network: dim=32, alpha=16 | LR: 1e-4 cosine | Epochs: 16"
echo ""

cd /workspace/sd-scripts
accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py \
    --config_file /workspace/train_winter_lora.toml

echo ""
echo "=== TRAINING COMPLETE ==="
echo "Output: /workspace/output/winter_girl_lora.safetensors"
echo "Download this file and bring it back to your local machine."
