#!/usr/bin/env python3
"""
Test the dashboard functionality
"""
import requests
import time
import sys

def test_dashboard():
    """Test if dashboard is accessible."""
    url = "http://localhost:8502"
    max_retries = 5
    
    print("Testing dashboard accessibility...")
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Dashboard is running at {url}")
                print(f"   Status Code: {response.status_code}")
                print(f"   Content Length: {len(response.content)} bytes")
                
                # Check for key elements
                content = response.text.lower()
                if "uruguay" in content:
                    print("   ✅ Uruguay content found")
                if "interview" in content:
                    print("   ✅ Interview content found")
                if "dashboard" in content:
                    print("   ✅ Dashboard content found")
                
                return True
        except requests.exceptions.RequestException as e:
            print(f"   Attempt {i+1}/{max_retries} failed: {str(e)}")
            time.sleep(2)
    
    print("❌ Dashboard test failed")
    return False

if __name__ == "__main__":
    success = test_dashboard()
    sys.exit(0 if success else 1)