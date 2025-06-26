import os
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

# Always load keys.env relative to this script's location
script_dir = Path(__file__).parent
keys_env_path = script_dir / "keys.env"
load_dotenv(keys_env_path)

# Load the Gemini API key from environment or prompt the user
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if not api_key:
    print("GOOGLE_GEMINI_API_KEY not found in environment. Please set it in your .env or keys.env file.")
    exit(1)

genai.configure(api_key=api_key)

print("\n🔍 Listing available Gemini models...")
try:
    models = genai.list_models()
    for model in models:
        print(f"- {model.name}")
except Exception as e:
    print(f"❌ Error listing models: {e}")
    exit(1)

# Try generating a simple response with the gemini-1.5-flash model
model_name = 'gemini-1.5-flash'
print(f"\n🔍 Testing model: {model_name}")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say hello, Gemini!")
    print(f"✅ Model response: {response.text.strip()}")
except Exception as e:
    print(f"❌ Error generating content with {model_name}: {e}") 