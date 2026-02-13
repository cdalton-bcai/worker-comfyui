# Winter LoRA Training Guide

## Prerequisites
- RunPod GPU pod (A40 48GB recommended, or RTX 4090 24GB)
- ~50GB disk space

## Quick Start

### 1. Launch a RunPod GPU Pod
- Template: **RunPod PyTorch 2.1** (or similar CUDA 12.x image)
- GPU: **A40** or **RTX 4090**
- Disk: **50 GB**

### 2. Upload Training Data
Upload the contents of `Winter Images (Lora)/` (all .png + .txt files) and `train_winter_lora.toml` to `/workspace/upload/` on the pod.

```bash
# From your local machine (use RunPod's file manager or SCP):
scp -P <PORT> "Winter Images (Lora)/"*.png "Winter Images (Lora)/"*.txt root@<POD_IP>:/workspace/upload/
scp -P <PORT> training/train_winter_lora.toml root@<POD_IP>:/workspace/upload/
```

### 3. Run Training
```bash
# Upload and run the training script
scp -P <PORT> training/run_training_runpod.sh root@<POD_IP>:/workspace/
ssh -p <PORT> root@<POD_IP> "chmod +x /workspace/run_training_runpod.sh && /workspace/run_training_runpod.sh"
```

### 4. Download Trained LoRA
```bash
scp -P <PORT> root@<POD_IP>:/workspace/output/winter_girl_lora.safetensors .
```

## Training Config Summary
| Parameter | Value |
|-----------|-------|
| Base model | Lustify v7 GGWP (SDXL) |
| Network dim (rank) | 32 |
| Network alpha | 16 |
| Learning rate | 1e-4 |
| Optimizer | AdamW8bit |
| LR scheduler | cosine |
| Epochs | 16 |
| Resolution | 1024x1024 (bucketed) |
| Mixed precision | bf16 |
| Images | 27 (27 repeats = 729 steps/epoch) |
| Trigger word | `winter_girl` |

## After Training
1. Copy `winter_girl_lora.safetensors` to the repo root
2. Uncomment the COPY line in `Dockerfile.custom`
3. Build: `docker build -f Dockerfile.custom -t <your-tag> .`
4. Push to Docker Hub and update RunPod template
