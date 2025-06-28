#!/usr/bin/env python3
"""
Test script to verify 502 error handling in the stock evaluation API
"""

import requests
import json
import time

def test_api_endpoint():
    """Test the API endpoint with various scenarios"""
    
    # Test configuration
    API_BASE_URL = "http://localhost:8000"
    test_ticker = "AAPL"
    
    # Test API keys (replace with your actual keys for testing)
    test_headers = {
        'X-FMP-API-Key': 'your_fmp_api_key_here',  # Replace with actual key
        'X-SERP-API-Key': 'your_serp_api_key_here',  # Replace with actual key
        'X-GEMINI-API-Key': 'your_gemini_api_key_here'  # Replace with actual key
    }
    
    print("Testing Stock Evaluation API Error Handling")
    print("=" * 50)
    
    # Test 1: Valid request
    print("\n1. Testing valid request...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/evaluate",
            json={"ticker": test_ticker, "include_detailed_analysis": True},
            headers=test_headers,
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Score: {result.get('composite_score', 'N/A')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Invalid API key (should return 401)
    print("\n2. Testing invalid API key...")
    try:
        invalid_headers = test_headers.copy()
        invalid_headers['X-FMP-API-Key'] = 'invalid_key'
        
        response = requests.post(
            f"{API_BASE_URL}/evaluate",
            json={"ticker": test_ticker, "include_detailed_analysis": True},
            headers=invalid_headers,
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✓ Correctly returned 401 for invalid API key")
        else:
            print(f"Unexpected response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Invalid ticker (should return 400 or 404)
    print("\n3. Testing invalid ticker...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/evaluate",
            json={"ticker": "INVALID_TICKER_123", "include_detailed_analysis": True},
            headers=test_headers,
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code in [400, 404]:
            print("✓ Correctly returned error for invalid ticker")
        else:
            print(f"Unexpected response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 4: Health check
    print("\n4. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"Health check failed: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 5: Rate limits check
    print("\n5. Testing rate limits endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/rate-limits", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            rate_data = response.json()
            print(f"Rate Limits: {rate_data.get('rate_limits', {})}")
        else:
            print(f"Rate limits check failed: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_web_app():
    """Test the web app endpoint"""
    
    WEB_APP_URL = "http://localhost:5000"
    test_ticker = "AAPL"
    
    print("\n" + "=" * 50)
    print("Testing Web App Error Handling")
    print("=" * 50)
    
    # Test web app evaluate endpoint
    print("\n1. Testing web app evaluate endpoint...")
    try:
        response = requests.post(
            f"{WEB_APP_URL}/evaluate",
            data={
                'ticker': test_ticker,
                'fmp_key': 'your_fmp_api_key_here',  # Replace with actual key
                'serp_key': 'your_serp_api_key_here',  # Replace with actual key
                'gemini_key': 'your_gemini_api_key_here'  # Replace with actual key
            },
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Web app request successful")
        else:
            print(f"Web app error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Stock Evaluation API Error Handling Test")
    print("Make sure both the API server (main.py) and web app (web_app.py) are running!")
    print()
    
    # Test API endpoint
    test_api_endpoint()
    
    # Test web app
    test_web_app()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("Check the logs for detailed error information.") 