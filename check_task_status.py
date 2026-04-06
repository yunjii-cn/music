import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"
TASK_ID = "8ec01181-cfe5-426a-bcf2-7ec038c88f8e"

print("=" * 60)
print("Auto-Label Task Status Check")
print("=" * 60)

for i in range(10):
    print(f"\n[Attempt {i+1}/10] Checking task status...")
    try:
        response = requests.get(f"{BASE_URL}/v1/dataset/auto_label_status/{TASK_ID}", timeout=10)
        result = response.json()
        data = result.get('data', {})
        
        status = data.get('status', 'unknown')
        progress = data.get('progress', 0)
        total = data.get('total', 0)
        error = data.get('error')
        
        print(f"Status: {status}")
        print(f"Progress: {progress}/{total}")
        
        if error:
            print(f"Error: {error}")
        
        if status == 'completed':
            print("\n✓ Auto-labeling completed!")
            print(f"Result: {json.dumps(data, indent=2, ensure_ascii=False)}")
            break
        elif status == 'failed':
            print("\n✗ Auto-labeling failed!")
            print(f"Error: {error}")
            break
        
        time.sleep(3)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)

print("\n" + "=" * 60)
