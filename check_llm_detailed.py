import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Check LLM Handler Status")
print("=" * 60)

# Check if LLM is initialized
print("\n[1] Checking LLM initialization via handler...")
try:
    response = requests.get(f"{BASE_URL}/v1/training/status", timeout=10)
    result = response.json()
    print(f"Training status: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Check dataset samples
print("\n[2] Checking dataset samples...")
try:
    response = requests.get(f"{BASE_URL}/v1/dataset/samples", timeout=10)
    result = response.json()
    samples = result.get('data', {}).get('samples', [])
    print(f"Total samples: {len(samples)}")
    for sample in samples:
        print(f"\n  Sample: {sample.get('filename')}")
        print(f"    Labeled: {sample.get('labeled')}")
        print(f"    Caption: {sample.get('caption', 'N/A')[:50]}...")
        print(f"    Is instrumental: {sample.get('is_instrumental')}")
except Exception as e:
    print(f"Error: {e}")

# Try to get more detailed error by checking the async task status
print("\n[3] Checking latest auto-label task status...")
try:
    response = requests.get(f"{BASE_URL}/v1/dataset/auto_label_status", timeout=10)
    result = response.json()
    print(f"Latest task: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
