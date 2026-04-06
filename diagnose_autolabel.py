import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Detailed Auto-Label Diagnosis")
print("=" * 60)

# 1. Clear dataset and rescan
print("\n[1] Clearing dataset...")
try:
    response = requests.post(f"{BASE_URL}/v1/dataset/clear", timeout=10)
    print(f"Clear status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# 2. Scan directory
print("\n[2] Scanning directory...")
scan_data = {
    "audio_dir": "E:/AI应用/qinglong-music-trainer-2.8.3/datasets",
    "dataset_name": "test_dataset",
    "custom_tag": "",
    "tag_position": "suffix",
    "all_instrumental": False
}

try:
    response = requests.post(f"{BASE_URL}/v1/dataset/scan", json=scan_data, timeout=30)
    result = response.json()
    print(f"Scan status: {response.status_code}")
    if response.status_code == 200:
        samples = result.get('data', {}).get('samples', [])
        print(f"Samples found: {len(samples)}")
        for s in samples:
            print(f"  - {s.get('filename')} (duration: {s.get('duration')}s)")
    else:
        print(f"Error: {result}")
except Exception as e:
    print(f"Error: {e}")

# 3. Try to encode audio to codes manually
print("\n[3] Testing audio encoding...")
try:
    response = requests.get(f"{BASE_URL}/v1/dataset/samples", timeout=10)
    result = response.json()
    samples = result.get('data', {}).get('samples', [])
    if samples:
        sample = samples[0]
        print(f"Testing with: {sample.get('filename')}")
        print(f"Audio path: {sample.get('audio_path')}")
        
        # Try to encode
        encode_data = {
            "audio_path": sample.get('audio_path')
        }
        response = requests.post(f"{BASE_URL}/v1/dataset/encode_audio", json=encode_data, timeout=60)
        print(f"Encode status: {response.status_code}")
        result = response.json()
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# 4. Try auto-label with verbose output
print("\n[4] Testing auto-label...")
auto_label_data = {
    "skip_metas": False,
    "format_lyrics": False,
    "transcribe_lyrics": False,
    "only_unlabeled": True
}

try:
    response = requests.post(f"{BASE_URL}/v1/dataset/auto_label_async", json=auto_label_data, timeout=10)
    result = response.json()
    task_id = result.get('data', {}).get('task_id')
    print(f"Task started: {task_id}")
    
    # Poll for status
    for i in range(20):
        time.sleep(3)
        status_response = requests.get(f"{BASE_URL}/v1/dataset/auto_label_status/{task_id}", timeout=10)
        status_result = status_response.json()
        data = status_result.get('data', {})
        
        status = data.get('status', 'unknown')
        progress = data.get('progress', '')
        print(f"  [{i+1}] Status: {status}, Progress: {progress[:100]}...")
        
        if status in ['completed', 'failed']:
            print(f"\nFinal result: {json.dumps(data, indent=2, ensure_ascii=False)}")
            break
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
