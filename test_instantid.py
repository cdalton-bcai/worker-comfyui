"""
Test script for InstantID face matching on RunPod endpoint.

Usage:
  python test_instantid.py <path_to_face_image>

Example:
  python test_instantid.py face_ref.png

The script will:
1. Base64-encode your reference face image
2. Send it to the RunPod endpoint with the InstantID workflow
3. Poll for completion
4. Save the output image as output_instantid.png
"""

import sys
import json
import base64
import time
import requests

# ---- Configuration ----
RUNPOD_API_KEY = "rpa_0O2C14CX1JRAUNCVDU6J4N7S6DJXGEJTPHIQQAE30g3v11"
ENDPOINT_ID = "tfijj06nammf3v"
BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_workflow(face_b64: str, prompt: str = None) -> dict:
    if prompt is None:
        prompt = (
            "RAW photo, portrait of a woman in a red dress, golden hour sunlight, "
            "detailed face, stunning beauty, skin texture, skin pores, 85mm lens, "
            "cinematic depth of field, natural lighting, photorealistic, 8k"
        )

    return {
        "input": {
            "workflow": {
                "1": {
                    "inputs": {"image": "face_ref.png", "upload": "image"},
                    "class_type": "LoadImage",
                },
                "2": {
                    "inputs": {"provider": "CPU"},
                    "class_type": "InstantIDFaceAnalysis",
                },
                "3": {
                    "inputs": {"ckpt_name": "lustifySDXLNSFW_ggwpV7.safetensors"},
                    "class_type": "CheckpointLoaderSimple",
                },
                "4": {
                    "inputs": {"instantid_file": "ip-adapter.bin"},
                    "class_type": "InstantIDModelLoader",
                },
                "5": {
                    "inputs": {"control_net_name": "instantid-controlnet.safetensors"},
                    "class_type": "ControlNetLoader",
                },
                "6": {
                    "inputs": {"text": prompt, "clip": ["3", 1]},
                    "class_type": "CLIPTextEncode",
                },
                "7": {
                    "inputs": {
                        "text": (
                            "(octane render, render, drawing, anime, bad photo, bad photography:1.3), "
                            "(worst quality, low quality, blurry:1.2), (bad teeth, deformed teeth, deformed lips), "
                            "(bad anatomy, bad proportions:1.1), (deformed iris, deformed pupils), "
                            "(deformed eyes, bad eyes), (deformed face, ugly face, bad face), "
                            "(deformed hands, bad hands, fused fingers), morbid, mutilated, mutation, "
                            "disfigured, extra limbs, extra legs, extra arms, duplicate, watermark, text"
                        ),
                        "clip": ["3", 1],
                    },
                    "class_type": "CLIPTextEncode",
                },
                "8": {
                    "inputs": {"width": 832, "height": 1216, "batch_size": 1},
                    "class_type": "EmptyLatentImage",
                },
                "9": {
                    "inputs": {
                        "instantid": ["4", 0],
                        "insightface": ["2", 0],
                        "control_net": ["5", 0],
                        "image": ["1", 0],
                        "model": ["3", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "weight": 0.8,
                        "start_at": 0.0,
                        "end_at": 1.0,
                    },
                    "class_type": "ApplyInstantID",
                },
                "10": {
                    "inputs": {
                        "seed": 42,
                        "steps": 35,
                        "cfg": 3.5,
                        "sampler_name": "dpmpp_2m_sde",
                        "scheduler": "karras",
                        "denoise": 1,
                        "model": ["9", 0],
                        "positive": ["9", 1],
                        "negative": ["9", 2],
                        "latent_image": ["8", 0],
                    },
                    "class_type": "KSampler",
                },
                "11": {
                    "inputs": {"samples": ["10", 0], "vae": ["3", 2]},
                    "class_type": "VAEDecode",
                },
                "12": {
                    "inputs": {"filename_prefix": "ComfyUI", "images": ["11", 0]},
                    "class_type": "SaveImage",
                },
            },
            "images": [{"name": "face_ref.png", "image": face_b64}],
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_instantid.py <path_to_face_image> [prompt]")
        sys.exit(1)

    face_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Encoding face image: {face_path}")
    face_b64 = encode_image(face_path)
    print(f"  Base64 size: {len(face_b64)} chars")

    payload = build_workflow(face_b64, prompt)

    print(f"Submitting job to {BASE_URL}/run ...")
    resp = requests.post(f"{BASE_URL}/run", json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    job = resp.json()
    job_id = job["id"]
    print(f"  Job ID: {job_id}")
    print(f"  Status: {job.get('status')}")

    # Poll for completion
    print("Polling for completion...")
    while True:
        time.sleep(5)
        status_resp = requests.get(
            f"{BASE_URL}/status/{job_id}", headers=HEADERS, timeout=30
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data.get("status")
        print(f"  Status: {status}")

        if status == "COMPLETED":
            output = status_data.get("output", {})
            images = output.get("images", [])
            if images:
                for i, img_info in enumerate(images):
                    img_data = img_info.get("data", "")
                    img_type = img_info.get("type", "base64")
                    filename = f"output_instantid_{i}.png"

                    if img_type == "base64":
                        with open(filename, "wb") as f:
                            f.write(base64.b64decode(img_data))
                        print(f"  Saved: {filename}")
                    elif img_type == "s3_url":
                        print(f"  S3 URL: {img_data}")
            else:
                print("  No images in output.")
                print(f"  Full output: {json.dumps(output, indent=2)}")
            break
        elif status == "FAILED":
            print(f"  Job failed: {json.dumps(status_data, indent=2)}")
            break
        elif status in ("IN_QUEUE", "IN_PROGRESS"):
            continue
        else:
            print(f"  Unknown status: {status}")
            print(f"  Full response: {json.dumps(status_data, indent=2)}")
            break

    print("Done.")


if __name__ == "__main__":
    main()
