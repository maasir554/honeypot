import requests
import json
import time
import os
import sys

def run_tests():
    # URL of your running API
    url = "http://localhost:8000/"
    
    # Check if scenarios file exists
    data_file = "tests/test_data_scenarios.json"
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        sys.exit(1)
        
    with open(data_file, "r") as f:
        scenarios = json.load(f)
        
    print(f"Loaded {len(scenarios)} scenarios from {data_file}")
    
    success_count = 0
    
    for i, scenario in enumerate(scenarios):
        name = scenario.get("scenarioName", f"Scenario {i+1}")
        payload = scenario.get("requestBody")
        
        print(f"\n--------------------------------------------------")
        print(f"Running: {name}")
        print(f"Payload Sender: {payload['message']['sender']}")
        print(f"Payload Text: {payload['message']['text']}")
        
        # Headers with x-test-mode to get synchronous intelligence
        headers = {
            "Content-Type": "application/json",
            "x-test-mode": "true",
            "x-api-key": os.getenv("API_KEY", "") # Pass API key if env var set, else empty (handled by API)
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Validations
            if data.get("status") != "success":
                print(f"❌ FAILED: Status is not success")
                continue
                
            reply = data.get("reply")
            if not reply:
                print(f"❌ FAILED: No reply from agent")
                continue
                
            print(f"✅ Agent Reply: {reply}")
            
            # Note: Intelligence extraction is async callback only now
            # You can check server logs for [Callback] output
            
            success_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: Request Error - {e}")
            if e.response:
                print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"❌ FAILED: Unexpected Error - {e}")
            
    print(f"\n--------------------------------------------------")
    print(f"Test Summary: {success_count}/{len(scenarios)} scenarios passed API check.")
    
if __name__ == "__main__":
    run_tests()
