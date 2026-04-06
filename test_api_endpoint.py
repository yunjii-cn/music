#!/usr/bin/env python3
"""Test API endpoint directly"""
import requests
import json

url = "http://127.0.0.1:8001/release_task"
headers = {"Content-Type": "application/json"}
data = {
    "prompt": "a happy pop song",
    "batch_size": 1,
    "inference_steps": 8,
    "audio_duration": 10,
    "guidance_scale": 7.0,
}

print("Sending request to API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
