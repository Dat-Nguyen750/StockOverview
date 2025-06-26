import requests
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv("keys.env")

def test_fmp_api():
    """Test if the FMP API key is working"""
    
    api_key = os.getenv("FMP_API_KEY")
    print(f"🔑 API Key loaded: {api_key is not None}")
    
    if api_key is None:
        print("❌ API Key is None - environment variable not loaded")
        print("Checking keys.env file...")
        
        # Try to read the file directly
        try:
            with open("keys.env", "r") as f:
                content = f.read()
                print("📄 keys.env content:")
                print(content)
        except Exception as e:
            print(f"❌ Error reading keys.env: {e}")
        return
    
    print(f"🔑 Testing FMP API Key: {api_key[:10]}...")
    print("=" * 50)
    
    # Test a simple endpoint
    url = "https://financialmodelingprep.com/api/v3/profile/AAPL"
    params = {"apikey": api_key}
    
    try:
        response = requests.get(url, params=params)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data:
                company = data[0]
                print("✅ API Key is working!")
                print(f"📊 Company: {company.get('companyName', 'N/A')}")
                print(f"💰 Market Cap: ${company.get('mktCap', 0):,.0f}")
                print(f"🏭 Industry: {company.get('industry', 'N/A')}")
            else:
                print("⚠️  API returned empty data")
        elif response.status_code == 401:
            print("❌ API Key is invalid or expired")
            print("Please check your FMP API key at: https://financialmodelingprep.com/developer/docs/")
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded")
            print("Please wait a moment and try again")
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

if __name__ == "__main__":
    test_fmp_api() 