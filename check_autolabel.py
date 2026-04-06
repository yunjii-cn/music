import requests
import json

print("=" * 60)
print("Auto-Label API Test")
print("=" * 60)

# Check LLM status via API
print("\n[1] Checking LLM initialization status...")
try:
    response = requests.get("http://127.0.0.1:8001/v1/training/status", timeout=5)
    data = response.json()
    print(f"Training status: {data.get('data', {}).get('status')}")
except Exception as e:
    print(f"Error: {e}")

# Try to get dataset status
print("\n[2] Checking dataset status...")
try:
    response = requests.get("http://127.0.0.1:8001/v1/dataset/status", timeout=5)
    print(f"Dataset status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Check if LLM is initialized
print("\n[3] Checking LLM handler status...")
try:
    response = requests.get("http://127.0.0.1:8001/v1/llm/status", timeout=5)
    print(f"LLM status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
