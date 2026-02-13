#!/bin/bash
set -e

echo "=== Winter LoRA Training Setup (RunPod) ==="
echo "Requires: A40 or 4090 GPU pod with ~48GB disk"

# ── 1. Install kohya sd-scripts ──────────────────────────────────
echo "[1/5] Installing kohya sd-scripts..."
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

# ── 2. Download base model + VAE ─────────────────────────────────
echo "[2/5] Downloading Lustify v7 checkpoint and VAE..."
mkdir -p /workspace/models

if [ ! -f "/workspace/models/lustifySDXLNSFW_ggwpV7.safetensors" ]; then
    wget -q --show-progress -O /workspace/models/lustifySDXLNSFW_ggwpV7.safetensors \
        "https://huggingface.co/Kutches/XL/resolve/main/lustifySDXLNSFW_ggwpV7.safetensors"
else
    echo "Lustify v7 already downloaded, skipping..."
fi

if [ ! -f "/workspace/models/sdxl-vae-fp16-fix.safetensors" ]; then
    wget -q --show-progress -O /workspace/models/sdxl-vae-fp16-fix.safetensors \
        "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors"
else
    echo "VAE already downloaded, skipping..."
fi

# ── 3. Set up dataset ────────────────────────────────────────────
echo "[3/5] Setting up dataset..."
# kohya format: dataset_dir/N_trigger_word/
# N = num_repeats (set in config, so use 1 here or match config)
mkdir -p /workspace/dataset/27_winter_girl

# Copy images + captions from uploaded folder
# You need to upload the "Winter Images (Lora)" folder to /workspace/upload/ first
if [ -d "/workspace/upload" ]; then
    cp /workspace/upload/*.png /workspace/dataset/27_winter_girl/
    cp /workspace/upload/*.txt /workspace/dataset/27_winter_girl/
    echo "Copied $(ls /workspace/dataset/27_winter_girl/*.png 2>/dev/null | wc -l) images"
    echo "Copied $(ls /workspace/dataset/27_winter_girl/*.txt 2>/dev/null | wc -l) captions"
else
    echo "WARNING: /workspace/upload/ not found!"
    echo "Upload your 'Winter Images (Lora)' folder contents to /workspace/upload/"
    echo "Then re-run this script."
    exit 1
fi

# ── 4. Create output directory ───────────────────────────────────
echo "[4/5] Creating output directories..."
mkdir -p /workspace/output
mkdir -p /workspace/logs

# ── 5. Launch training ───────────────────────────────────────────
echo "[5/5] Starting LoRA training..."
echo "Config: network_dim=32, network_alpha=16, lr=1e-4, epochs=16"
echo "Estimated time: ~30-45 min on A40, ~20-30 min on 4090"
echo ""

cd /workspace/sd-scripts

# Copy training config
cp /workspace/upload/train_winter_lora.toml /workspace/train_winter_lora.toml 2>/dev/null || true

accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py \
    --config_file /workspace/train_winter_lora.toml

echo ""
echo "=== Training Complete ==="
echo "Output: /workspace/output/winter_girl_lora.safetensors"
echo ""
echo "Next steps:"
echo "1. Download winter_girl_lora.safetensors from /workspace/output/"
echo "2. Copy it to your local repo"
echo "3. Update Dockerfile.custom to COPY it into the image"
echo "4. Build and push the Docker image"
