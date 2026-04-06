import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Direct LLM Test")
print("=" * 60)

# Test LLM directly with audio codes
print("\n[1] Testing LLM with sample audio codes...")
test_codes = "<|audio_code_10000|><|audio_code_20000|><|audio_code_30000|>"

try:
    response = requests.post(
        f"{BASE_URL}/v1/llm/understand",
        json={"audio_codes": test_codes, "temperature": 0.7},
        timeout=60
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
except Exception as e:
    print(f"Error: {e}")

# Check if there's a direct LLM endpoint
print("\n[2] Checking available LLM endpoints...")
try:
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
    result = response.json()
    paths = result.get('paths', {})
    llm_endpoints = [p for p in paths.keys() if 'llm' in p.lower()]
    print(f"LLM endpoints: {llm_endpoints}")
except Exception as e:
    print(f"Error: {e}")

# Check generation endpoint
print("\n[3] Testing generation endpoint...")
try:
    response = requests.post(
        f"{BASE_URL}/v1/generate",
        json={
            "prompt": "test",
            "duration": 10,
            "infer_step": 1
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
