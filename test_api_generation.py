#!/usr/bin/env python3
"""Test API server generation directly"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("ACE-Step API Server Test")
print("=" * 60)

# Test 1: Check if handler can be initialized
print("\n[1] Testing handler initialization...")
try:
    from acestep.handler import AceStepHandler
    handler = AceStepHandler()
    print("Handler created successfully")
    
    # Test initialization
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = "acestep-v15-turbo"
    
    print(f"Initializing service with config_path={config_path}...")
    status_msg, ok = handler.initialize_service(
        project_root=project_root,
        config_path=config_path,
        device="auto",
        use_flash_attention=True,
        offload_to_cpu=True,
    )
    
    if ok:
        print(f"Handler initialized successfully: {status_msg}")
    else:
        print(f"Handler initialization failed: {status_msg}")
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check if model is loaded
print("\n[2] Checking model status...")
if hasattr(handler, 'model') and handler.model is not None:
    print("Model loaded successfully")
    print(f"Model type: {type(handler.model)}")
else:
    print("Model not loaded!")

if hasattr(handler, 'vae') and handler.vae is not None:
    print("VAE loaded successfully")
else:
    print("VAE not loaded!")

if hasattr(handler, 'text_encoder') and handler.text_encoder is not None:
    print("Text encoder loaded successfully")
else:
    print("Text encoder not loaded!")

# Test 3: Test simple generation
print("\n[3] Testing simple generation...")
try:
    from acestep.inference import GenerationParams, generate_music
    
    params = GenerationParams(
        prompt="a happy pop song",
        audio_duration=10,
        batch_size=1,
        inference_steps=8,
        guidance_scale=7.0,
    )
    
    print("Starting generation...")
    print(f"Parameters: prompt='{params.prompt}', duration={params.audio_duration}s")
    
    # This might take a while
    result = generate_music(handler, params)
    
    if result and result.get("audio_paths"):
        print(f"Generation successful! Audio files: {result['audio_paths']}")
    else:
        print(f"Generation returned no audio: {result}")
        
except Exception as e:
    print(f"Generation error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
