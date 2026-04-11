import sys
print(f"Python: {sys.version}")
print()

modules = [
    "torch",
    "torchvision",
    "torchaudio",
    "transformers",
    "diffusers",
    "gradio",
    "loguru",
    "fastapi",
    "uvicorn",
    "einops",
    "accelerate",
]

for module in modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {e}")
        import traceback
        traceback.print_exc()
    print()

print()
print("尝试导入 acestep.api_server...")
try:
    import acestep.api_server
    print("✅ acestep.api_server 导入成功")
except Exception as e:
    print(f"❌ acestep.api_server 导入失败: {e}")
    import traceback
    traceback.print_exc()
