#!/usr/bin/env python3
"""Check API server configuration"""
import requests
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("ACE-Step API Server Configuration Check")
print("=" * 60)

# Check environment variables
print("\n[Environment Variables]")
env_vars = [
    "ACESTEP_CONFIG_PATH",
    "ACESTEP_DEVICE",
    "ACESTEP_OFFLOAD_TO_CPU",
    "ACESTEP_OFFLOAD_DIT_TO_CPU",
    "ACESTEP_INIT_LLM",
    "ACESTEP_LM_MODEL_PATH",
    "ACESTEP_LM_BACKEND",
    "ACESTEP_USE_FLASH_ATTENTION",
]

for var in env_vars:
    value = os.environ.get(var, "(not set)")
    print(f"  {var}: {value}")

# Check .env file
print("\n[.env File]")
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    print(f"  Found: {env_file}")
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                print(f"  {line}")
else:
    print(f"  Not found: {env_file}")

# Check GPU memory
print("\n[GPU Memory]")
try:
    import torch
    if torch.cuda.is_available():
        print(f"  CUDA available: True")
        print(f"  Device: {torch.cuda.get_device_name(0)}")
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        free = total - reserved
        print(f"  Total: {total:.2f} GB")
        print(f"  Allocated: {allocated:.2f} GB")
        print(f"  Reserved: {reserved:.2f} GB")
        print(f"  Free: {free:.2f} GB")
        
        if free < 2:
            print("\n  ⚠️ WARNING: GPU memory is almost full!")
            print("  Recommended: Enable ACESTEP_OFFLOAD_TO_CPU=true")
    else:
        print("  CUDA not available")
except Exception as e:
    print(f"  Error: {e}")

# Check API server status
print("\n[API Server Status]")
try:
    response = requests.get("http://127.0.0.1:8001/health", timeout=5)
    print(f"  Health: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
