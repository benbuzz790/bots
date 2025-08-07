#!/usr/bin/env python3
"""
Debug REST API bot creation issue
"""

import requests
import json

def test_rest_api():
    """Test REST API bot creation with detailed error info."""
    print("Testing REST API bot creation...")

    try:
        url = "http://127.0.0.1:8000/api/bots/create"
        payload = {"name": "Test Bot"}

        print(f"Making request to: {url}")
        print(f"Payload: {payload}")

        response = requests.post(url, json=payload)

        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success! Bot ID: {data.get('bot_id')}")
            return True
        else:
            print("❌ Request failed")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print("Could not parse error response as JSON")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rest_api()
    if success:
        print("\n🎉 REST API test passed!")
    else:
        print("\n❌ REST API test failed!")