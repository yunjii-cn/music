#!/usr/bin/env python3
"""Query task result"""
import requests
import json
import time

task_id = "9fe134da-54de-4cd7-8a22-8517cffc4018"
url = "http://127.0.0.1:8001/query_result"
headers = {"Content-Type": "application/json"}
data = {"task_id_list": [task_id]}

print(f"Querying task: {task_id}")

for i in range(30):  # Check for 30 iterations
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        
        task_data = result.get("data", [{}])[0] if result.get("data") else {}
        status = task_data.get("status", "unknown")
        
        print(f"\n[{i+1}/30] Status: {status}")
        
        if status == 1:  # Done
            print("Task completed!")
            print(json.dumps(result, indent=2))
            break
        elif status == 2:  # Failed
            print("Task failed!")
            print(json.dumps(result, indent=2))
            break
        else:
            print(f"Task still processing... (status={status})")
            if task_data.get("result"):
                print(f"Progress info: {task_data.get('result')}")
            time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
