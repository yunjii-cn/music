import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Debug Auto-Label Failure")
print("=" * 60)

# Get current samples
print("\n[1] Getting current samples...")
try:
    response = requests.get(f"{BASE_URL}/v1/dataset/samples", timeout=10)
    result = response.json()
    samples = result.get('data', {}).get('samples', [])
    print(f"Total samples: {len(samples)}")
    for i, sample in enumerate(samples):
        print(f"\nSample {i}:")
        print(f"  Filename: {sample.get('filename')}")
        print(f"  Audio path: {sample.get('audio_path')}")
        print(f"  Duration: {sample.get('duration')}")
        print(f"  Labeled: {sample.get('labeled')}")
        print(f"  Caption: {sample.get('caption', 'N/A')}")
        print(f"  Genre: {sample.get('genre', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Try synchronous auto-label to get immediate error
print("\n[2] Trying synchronous auto-label...")
auto_label_data = {
    "skip_metas": False,
    "format_lyrics": False,
    "transcribe_lyrics": False,
    "only_unlabeled": True
}

try:
    response = requests.post(f"{BASE_URL}/v1/dataset/auto_label", json=auto_label_data, timeout=120)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
