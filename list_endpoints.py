import requests
import json

BASE_URL = "http://127.0.0.1:8001"

print("=" * 60)
print("All Available API Endpoints")
print("=" * 60)

try:
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
    result = response.json()
    paths = result.get('paths', {})
    
    print(f"\nTotal endpoints: {len(paths)}")
    print("\nEndpoints:")
    for path, methods in sorted(paths.items()):
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'delete']:
                summary = details.get('summary', '')
                print(f"  [{method.upper()}] {path} - {summary}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
