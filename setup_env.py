#!/usr/bin/env python3
"""
Setup script for Stock Evaluation API
This script helps you configure your API keys
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with API key placeholders"""
    
    env_content = """# Stock Evaluation API - Environment Configuration
# Replace the placeholder values with your actual API keys

# Financial Modeling Prep API Key (Required)
# Get your free key at: https://financialmodelingprep.com/developer/docs/
FMP_API_KEY=your_fmp_api_key_here

# SERP API Key (Optional - for news and search)
# Get your key at: https://serpapi.com/
SERP_API_KEY=your_serp_api_key_here

# Google Gemini API Key (Required for AI analysis)
# Get your key at: https://makersuite.google.com/app/apikey
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here

# Configuration
FMP_RATE_LIMIT_PER_MINUTE=15
DEBUG=True
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print("\n📝 Next steps:")
    print("1. Edit the .env file and replace the placeholder values with your actual API keys")
    print("2. At minimum, you need FMP_API_KEY and GOOGLE_GEMINI_API_KEY")
    print("3. SERP_API_KEY is optional but recommended for better analysis")
    print("\n🔗 Get your API keys from:")
    print("   • FMP: https://financialmodelingprep.com/developer/docs/")
    print("   • Gemini: https://makersuite.google.com/app/apikey")
    print("   • SERP: https://serpapi.com/")

def check_env_setup():
    """Check if environment is properly configured"""
    
    required_keys = ['FMP_API_KEY', 'GOOGLE_GEMINI_API_KEY']
    optional_keys = ['SERP_API_KEY']
    
    print("🔍 Checking environment configuration...")
    print("=" * 50)
    
    all_good = True
    
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower()}_here":
            print(f"❌ {key}: Not configured")
            all_good = False
        else:
            print(f"✅ {key}: Configured")
    
    for key in optional_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower()}_here":
            print(f"⚠️  {key}: Not configured (optional)")
        else:
            print(f"✅ {key}: Configured")
    
    print("=" * 50)
    
    if all_good:
        print("🎉 Environment is properly configured!")
        print("You can now run the API with: python main.py")
    else:
        print("❌ Please configure the required API keys in your .env file")
        print("Run this script again to create a new .env file")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_env_setup()
    else:
        create_env_file() 