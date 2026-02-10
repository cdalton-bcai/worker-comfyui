"""
Test script for enhanced face matching: InstantID + FaceID V2 + FaceDetailer.

Usage:
  python test_enhanced.py <path_to_face_image> [prompt]
"""

import sys
import json
import base64
import time
import requests

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

    negative = (
        "(worst quality, low quality, blurry:1.2), (bad anatomy, bad proportions:1.1), "
        "(deformed face, ugly face), (deformed hands, bad hands, fused fingers), watermark, text"
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
                    "inputs": {"text": negative, "clip": ["3", 1]},
                    "class_type": "CLIPTextEncode",
                },
                "8": {
                    "inputs": {"width": 832, "height": 1216, "batch_size": 1},
                    "class_type": "EmptyLatentImage",
                },
                "20": {
                    "inputs": {
                        "preset": "FACEID PLUS V2",
                        "model": ["3", 0],
                    },
                    "class_type": "IPAdapterUnifiedLoaderFaceID",
                },
                "21": {
                    "inputs": {
                        "weight": 0.7,
                        "weight_type": "linear",
                        "start_at": 0.0,
                        "end_at": 1.0,
                        "image": ["1", 0],
                        "model": ["20", 0],
                        "ipadapter": ["20", 1],
                    },
                    "class_type": "IPAdapterFaceID",
                },
                "9": {
                    "inputs": {
                        "instantid": ["4", 0],
                        "insightface": ["2", 0],
                        "control_net": ["5", 0],
                        "image": ["1", 0],
                        "model": ["21", 0],
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
                "30": {
                    "inputs": {"model_name": "bbox/face_yolov8m.pt"},
                    "class_type": "UltralyticsDetectorProvider",
                },
                "31": {
                    "inputs": {
                        "guide_size": 512,
                        "guide_size_for": True,
                        "max_size": 1024,
                        "seed": 42,
                        "steps": 20,
                        "cfg": 3.5,
                        "sampler_name": "dpmpp_2m_sde",
                        "scheduler": "karras",
                        "denoise": 0.35,
                        "feather": 5,
                        "noise_mask": True,
                        "force_inpaint": True,
                        "bbox_threshold": 0.5,
                        "bbox_dilation": 10,
                        "bbox_crop_factor": 3.0,
                        "sam_detection_hint": "center-1",
                        "sam_dilation": 0,
                        "sam_threshold": 0.93,
                        "sam_bbox_expansion": 0,
                        "sam_mask_hint_threshold": 0.7,
                        "sam_mask_hint_use_negative": "False",
                        "drop_size": 10,
                        "wildcard": "",
                        "cycle": 1,
                        "image": ["11", 0],
                        "model": ["3", 0],
                        "clip": ["3", 1],
                        "vae": ["3", 2],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "bbox_detector": ["30", 0],
                    },
                    "class_type": "FaceDetailer",
                },
                "12": {
                    "inputs": {"filename_prefix": "ComfyUI", "images": ["31", 0]},
                    "class_type": "SaveImage",
                },
            },
            "images": [{"name": "face_ref.png", "image": face_b64}],
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_enhanced.py <path_to_face_image> [prompt]")
        sys.exit(1)

    face_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Encoding face image: {face_path}")
    face_b64 = encode_image(face_path)
    print(f"  Base64 size: {len(face_b64)} chars")

    payload = build_workflow(face_b64, prompt)

    print(f"Submitting enhanced workflow to {BASE_URL}/run ...")
    resp = requests.post(f"{BASE_URL}/run", json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    job = resp.json()
    job_id = job["id"]
    print(f"  Job ID: {job_id}")

    print("Polling for completion...")
    while True:
        time.sleep(5)
        sr = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS, timeout=30)
        sd = sr.json()
        status = sd.get("status")
        print(f"  Status: {status}")

        if status == "COMPLETED":
            output = sd.get("output", {})
            images = output.get("images", [])
            if images:
                for i, img_info in enumerate(images):
                    img_data = img_info.get("data", "")
                    filename = f"output_enhanced_{i}.png"
                    with open(filename, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    print(f"  Saved: {filename}")
            else:
                print("  No images in output.")
                print(f"  Output: {json.dumps(output, indent=2)[:1000]}")
            break
        elif status == "FAILED":
            print(f"  FAILED: {sd.get('error', json.dumps(sd, indent=2)[:1000])}")
            break

    print("Done.")


if __name__ == "__main__":
    main()
