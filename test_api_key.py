"""Quick test to verify Gemini API key and available models"""
import google.generativeai as genai
from config import GOOGLE_API_KEY, GEMINI_MODEL

print("Testing Gemini API connection...")
print(f"API Key: {GOOGLE_API_KEY[:15]}...")
print(f"Model: {GEMINI_MODEL}")
print()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # List available models
    print("Available models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    print("\nTesting generateContent with first available model...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello in one word")
    print(f"Response: {response.text}")
    print("\n✅ API key works!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible issues:")
    print("  • API key is invalid")
    print("  • API key doesn't have proper permissions")  
    print("  • Gemini API is not enabled for this key")
