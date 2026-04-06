import requests
import json

# Check API health
print("=" * 60)
print("API Service Status Check")
print("=" * 60)

# Health check
try:
    response = requests.get("http://127.0.0.1:8001/health", timeout=5)
    print(f"\n[Health] Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"[Health] Error: {e}")

# Check models
try:
    response = requests.get("http://127.0.0.1:8001/v1/models", timeout=5)
    print(f"\n[Models] Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"[Models] Error: {e}")

# Check training status (LLM status)
try:
    response = requests.get("http://127.0.0.1:8001/v1/training/status", timeout=5)
    print(f"\n[Training Status] Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"[Training Status] Error: {e}")

print("\n" + "=" * 60)
