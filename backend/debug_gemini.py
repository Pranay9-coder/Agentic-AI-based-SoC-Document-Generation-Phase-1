"""
Debug script to list available Gemini models
Run this to see which models your API key has access to
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✓ Using API key: {api_key[:10]}...{api_key[-5:]}")
print()

# Configure Gemini
genai.configure(api_key=api_key)

print("=" * 70)
print("📋 AVAILABLE GEMINI MODELS")
print("=" * 70)
print()

try:
    models = genai.list_models()
    
    generate_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            generate_models.append(model)
            print(f"✓ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Input Token Limit: {model.input_token_limit:,}")
            print(f"   Output Token Limit: {model.output_token_limit:,}")
            print()
    
    if not generate_models:
        print("❌ No models found that support 'generateContent'")
    else:
        print("=" * 70)
        print(f"Found {len(generate_models)} model(s) that support content generation")
        print("=" * 70)
        print()
        print("🔧 RECOMMENDED MODELS TO TRY:")
        print()
        
        # Find best models
        flash_models = [m for m in generate_models if 'flash' in m.name.lower()]
        pro_models = [m for m in generate_models if 'pro' in m.name.lower()]
        
        if flash_models:
            print("1. Flash Models (Fast & Efficient):")
            for m in flash_models:
                print(f"   - {m.name}")
        
        if pro_models:
            print()
            print("2. Pro Models (Higher Quality):")
            for m in pro_models:
                print(f"   - {m.name}")
        
        print()
        print("💡 TIP: Copy one of the model names above and use it in your code")
        
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print()
    print("Possible reasons:")
    print("1. Invalid API key")
    print("2. API key doesn't have proper permissions")
    print("3. Network connectivity issue")
    print("4. Need to upgrade google-generativeai library: pip install --upgrade google-generativeai")