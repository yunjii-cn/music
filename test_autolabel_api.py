import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Auto-Label API Detailed Test")
print("=" * 60)

# 1. Scan directory to create dataset
print("\n[1] Scanning directory for audio files...")
scan_data = {
    "audio_dir": "E:/AI应用/qinglong-music-trainer-2.8.3/test_audio",
    "dataset_name": "test_dataset",
    "custom_tag": "",
    "tag_position": "suffix",
    "all_instrumental": False
}

try:
    response = requests.post(f"{BASE_URL}/v1/dataset/scan", json=scan_data, timeout=30)
    print(f"Scan status: {response.status_code}")
    result = response.json()
    if response.status_code == 200:
        print(f"Samples found: {len(result.get('data', {}).get('samples', []))}")
    else:
        print(f"Error: {result}")
except Exception as e:
    print(f"Error: {e}")

# 2. Check dataset status
print("\n[2] Checking dataset status...")
try:
    response = requests.get(f"{BASE_URL}/v1/dataset/samples", timeout=10)
    print(f"Dataset status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        samples = result.get('data', {}).get('samples', [])
        print(f"Total samples: {len(samples)}")
        if samples:
            print(f"First sample: {samples[0].get('filename', 'N/A')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 3. Try auto-label (just check if API responds)
print("\n[3] Testing auto-label API endpoint...")
auto_label_data = {
    "skip_metas": False,
    "format_lyrics": False,
    "transcribe_lyrics": False,
    "only_unlabeled": True
}

try:
    response = requests.post(f"{BASE_URL}/v1/dataset/auto_label_async", json=auto_label_data, timeout=10)
    print(f"Auto-label status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
