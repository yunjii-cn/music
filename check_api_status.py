#!/usr/bin/env python3
"""Check API server status"""
import requests
import json

# Check health
print("=" * 60)
print("API Server Status Check")
print("=" * 60)

# Health check
try:
    response = requests.get("http://127.0.0.1:8001/health", timeout=5)
    print(f"\n[Health] Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"[Health] Error: {e}")

# Models check
try:
    response = requests.get("http://127.0.0.1:8001/v1/models", timeout=5)
    print(f"\n[Models] Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"[Models] Error: {e}")

# Check GPU
print("\n[GPU Status]")
try:
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        print(f"CUDA memory allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        print(f"CUDA memory reserved: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")
except Exception as e:
    print(f"GPU check error: {e}")

# Check if model is loaded
print("\n[Model Status]")
try:
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Try to get handler status via API
    response = requests.get("http://127.0.0.1:8001/v1/training/status", timeout=5)
    print(f"Training status: {response.json()}")
except Exception as e:
    print(f"Model status check error: {e}")

print("\n" + "=" * 60)
