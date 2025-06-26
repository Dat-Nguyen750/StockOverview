import requests
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv("keys.env")

def test_fmp_endpoints():
    """Test different FMP endpoints to see which ones work"""
    
    api_key = os.getenv("FMP_API_KEY")
    base_url = "https://financialmodelingprep.com/api/v3"
    
    # Test different endpoints
    endpoints = [
        ("profile", f"{base_url}/profile/AAPL"),
        ("quote", f"{base_url}/quote/AAPL"),
        ("income-statement", f"{base_url}/income-statement/AAPL"),
        ("key-metrics", f"{base_url}/key-metrics/AAPL"),
        ("ratios", f"{base_url}/ratios/AAPL"),
        ("analyst-estimates", f"{base_url}/analyst-estimates/AAPL")
    ]
    
    print(f"🔑 Testing FMP API Key: {api_key[:10]}...")
    print("=" * 60)
    
    working_endpoints = []
    
    for name, url in endpoints:
        params = {"apikey": api_key}
        
        try:
            response = requests.get(url, params=params)
            status = response.status_code
            
            if status == 200:
                data = response.json()
                print(f"✅ {name}: {status} - {len(data) if isinstance(data, list) else 'OK'}")
                working_endpoints.append(name)
            elif status == 401:
                print(f"❌ {name}: {status} - Unauthorized (invalid key)")
            elif status == 403:
                print(f"🚫 {name}: {status} - Forbidden (requires subscription)")
            elif status == 429:
                print(f"⏳ {name}: {status} - Rate limited")
            else:
                print(f"❓ {name}: {status} - {response.text[:50]}")
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
    
    print("=" * 60)
    print(f"📊 Working endpoints: {len(working_endpoints)}/{len(endpoints)}")
    if working_endpoints:
        print(f"✅ Available: {', '.join(working_endpoints)}")
    else:
        print("❌ No endpoints working - API key issue")

if __name__ == "__main__":
    test_fmp_endpoints() 