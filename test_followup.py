#!/usr/bin/env python
"""
Test script for /followup endpoint
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_followup():
    """Test the /followup endpoint"""
    
    # First, test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   Server may not be running. Start it with: python run.py")
        return False
    
    # Test followup endpoint
    print("\n2. Testing /followup endpoint...")
    
    followup_data = {
        "question": "Can you explain what elevated cholesterol means?"
    }
    
    headers = {
        "X-Session-ID": "test-session-123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/followup",
            data=followup_data,
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("message") and "LLM" not in result.get("message", "").upper():
                print("\n✓ SUCCESS: Received LLM response from /followup endpoint!")
                print(f"   Message: {result['message'][:200]}...")
                return True
            else:
                print("\n✗ FAILED: Response doesn't look like LLM output")
                return False
        else:
            print(f"\n✗ FAILED: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_followup()
    sys.exit(0 if success else 1)
