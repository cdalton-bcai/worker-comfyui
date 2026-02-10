# ComfyUI RunPod Deployment Plan

## Current Setup
- **Image:** `cdaltonbcai/comfyui-sdxl:v2-epicrealism`
- **Model:** epiCRealism XL (photorealistic, uncensored SDXL)
- **Endpoint:** `https://api.runpod.ai/v2/tfijj06nammf3v/run`
- **API Key:** `rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101`
- **Status:** Working, text-to-image only (no face/body matching)

## Optimal Settings (epiCRealism XL)
| Setting | Value |
|---|---|
| Sampler | `dpmpp_2m` |
| Scheduler | `karras` |
| CFG | 5-6 |
| Steps | 30-40 |
| Resolution (portrait) | 832x1216 |
| Resolution (landscape) | 1216x832 |
| Resolution (square) | 1024x1024 |
| Checkpoint | `epicrealism-xl.safetensors` |

---

## Phased Upgrade Plan

### Phase 1: Face Matching (Next)
**Goal:** Send a reference face photo, get images with that face matched.

**What gets baked into Docker image (one-time):**
- Custom nodes (all installed now, used incrementally):
  - `ComfyUI_IPAdapter_plus` (IP-Adapter FaceID)
  - `ComfyUI_InstantID` (InstantID face transfer)
  - `comfyui_controlnet_aux` (ControlNet preprocessors)
- Face models:
  - InsightFace `antelopev2` (face detection/embedding)
  - CLIP Vision encoder (`CLIP-ViT-H-14-laion2B-s32B-b79K`)
  - InstantID model (`ip-adapter_instant_id_sdxl.bin`)
  - InstantID ControlNet (`control_instant_id_sdxl.safetensors`)
- Existing models (already in image):
  - epiCRealism XL checkpoint
  - SDXL VAE fp16 fix

**How it works:**
1. Send a reference face image + text prompt via API
2. InstantID extracts face identity from reference
3. epiCRealism XL generates the image guided by face identity + prompt
4. Result: photorealistic image with your specific face

**Workflow changes:**
- API request includes `images` field with base64-encoded reference face
- Workflow nodes: LoadImage → InstantID → KSampler → SaveImage

**Estimated rebuild time:** ~20-30 min (build + push)

---

### Phase 2: Pose Control (Later - No Docker Rebuild)
**Goal:** Control exact pose of generated character.

**What to add:**
- ControlNet OpenPose model for SDXL (~2.5GB)
- Upload to RunPod Network Volume (no Docker rebuild needed)

**How it works:**
1. Send reference face + reference pose image
2. InstantID handles face, ControlNet handles pose
3. Result: your face + exact pose you specified

**Nodes already installed in Phase 1:** ControlNet preprocessors + ControlNet apply nodes

---

### Phase 3: Full Character Lock via LoRA (Later - No Docker Rebuild)
**Goal:** Lock in face + body type + skin + overall character look.

**What to do:**
1. Collect 15-20 reference photos of your character (various angles, lighting)
2. Train a LoRA on RunPod or CivitAI (~20 min training)
3. Upload the LoRA file (~200MB) to RunPod Network Volume

**How it works:**
1. LoRA locks body type, skin tone, character features
2. InstantID locks face identity
3. ControlNet locks pose
4. Text prompt controls scene, clothing, action
5. Result: "Triple-Lock" — fully consistent character across all generations

**Nodes already installed in Phase 1:** LoRA loader nodes are built into ComfyUI base

---

## Architecture Notes

### Why phased works without redo
- **Custom nodes** are tiny (~50MB total) — install ALL in Phase 1
- **Additional models** (ControlNet, LoRAs) go on **RunPod Network Volume**
- Docker image only needs rebuilding if changing the base checkpoint model
- Each phase adds capability without touching previous work

### RunPod Network Volume (for Phase 2+)
- Create a network volume in RunPod
- Upload ControlNet models, LoRAs, etc. to `/runpod-volume/models/`
- Attach to your serverless endpoint
- Models auto-discovered by ComfyUI via `extra_model_paths.yaml`

### Face Transfer Methods Comparison
| Method | Face Accuracy | Speed | Extra VRAM | Notes |
|---|---|---|---|---|
| IP-Adapter FaceID | ~80% | Fastest | +1-2GB | Simplest, broadest compat |
| InstantID | ~90% | Medium | +2-3GB | Best balance, proven SDXL |
| PuLID | ~95% | Slowest | +3-4GB | Best accuracy, most complex |

### Body Consistency Methods
| Method | What it controls | Effort |
|---|---|---|
| Detailed prompts | Approximate body description | None |
| ControlNet OpenPose | Exact pose | Low (add model file) |
| Character LoRA | Body type, skin, overall look | Medium (train LoRA) |
| Triple-Lock (all three) | Everything | Full setup |

---

## API Usage

### Submit job (text-to-image, current)
```bash
curl -X POST https://api.runpod.ai/v2/tfijj06nammf3v/run \
  -H "Authorization: Bearer rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101" \
  -H "Content-Type: application/json" \
  -d '{"input":{"workflow":{...}}}'
```

### Submit job (with face reference, Phase 1)
```bash
curl -X POST https://api.runpod.ai/v2/tfijj06nammf3v/run \
  -H "Authorization: Bearer rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101" \
  -H "Content-Type: application/json" \
  -d '{"input":{"workflow":{...},"images":[{"name":"face_ref.png","image":"BASE64_ENCODED_IMAGE"}]}}'
```

### Check job status
```bash
curl https://api.runpod.ai/v2/tfijj06nammf3v/status/JOB_ID \
  -H "Authorization: Bearer rpa_C0DVYI5FODZT1X9V1J1BN7HSCI3Z02350B7O836N3sw101"
```

### Response format
```json
{
  "id": "JOB_ID",
  "status": "COMPLETED",
  "output": {
    "images": [
      {
        "filename": "ComfyUI_00001_.png",
        "type": "base64",
        "data": "<base64 PNG>"
      }
    ]
  }
}
```

---

## Key Files
- `Dockerfile.custom` — Custom Dockerfile (rebuild target)
- `test_input_sdxl.json` — Test workflow (text-to-image)
- `DEPLOYMENT_PLAN.md` — This file
