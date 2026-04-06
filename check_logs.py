import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("Check API Server Logs")
print("=" * 60)

# Check if there's a log endpoint
try:
    response = requests.get(f"{BASE_URL}/v1/logs", timeout=10)
    print(f"Logs status: {response.status_code}")
    print(f"Logs: {response.text[:1000]}")
except Exception as e:
    print(f"No logs endpoint: {e}")

# Check debug info
try:
    response = requests.get(f"{BASE_URL}/debug", timeout=10)
    print(f"\nDebug status: {response.status_code}")
    print(f"Debug: {response.text[:1000]}")
except Exception as e:
    print(f"No debug endpoint: {e}")

# Check model status
print("\n[Model Status]")
try:
    response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
    result = response.json()
    print(f"Models: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
