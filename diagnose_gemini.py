#!/usr/bin/env python3
"""
Comprehensive Gemini Diagnostics and Fix
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_gemini():
    """Comprehensive Gemini diagnostics"""
    print("🔍 Comprehensive Gemini Diagnostics")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # 1. Check environment variables
    print("\n1️⃣ Environment Check:")
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"   API Key exists: {bool(api_key)}")
    if api_key:
        print(f"   API Key format: {api_key[:15]}...")
        print(f"   Starts with 'AIza': {api_key.startswith('AIza')}")
        print(f"   Length: {len(api_key)}")
    
    # 2. Check library installation
    print("\n2️⃣ Library Check:")
    try:
        import google.generativeai as genai
        print("   ✅ google.generativeai imported successfully")
        print(f"   Version: {getattr(genai, '__version__', 'Unknown')}")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # 3. Check network connectivity
    print("\n3️⃣ Network Check:")
    try:
        import requests
        response = requests.get("https://generativelanguage.googleapis.com", timeout=10)
        print(f"   ✅ Can reach Google AI endpoint (status: {response.status_code})")
    except Exception as e:
        print(f"   ⚠️ Network issue: {e}")
    
    # 4. Test configuration
    print("\n4️⃣ Configuration Test:")
    if not api_key:
        print("   ❌ Cannot test - no API key")
        return False
    
    try:
        genai.configure(api_key=api_key)
        print("   ✅ Configuration successful")
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False
    
    # 5. Test model creation
    print("\n5️⃣ Model Creation Test:")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("   ✅ Model created successfully")
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        return False
    
    # 6. Test simple generation with timeout
    print("\n6️⃣ Generation Test:")
    try:
        import concurrent.futures
        
        def make_request():
            return model.generate_content("Say 'Hello' in one word")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(make_request)
            try:
                response = future.result(timeout=30)  # 30 second timeout
                if response and response.text:
                    print(f"   ✅ Generation successful: '{response.text.strip()}'")
                    return True
                else:
                    print("   ❌ Empty response")
                    return False
            except concurrent.futures.TimeoutError:
                print("   ❌ Request timed out (30s)")
                return False
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = diagnose_gemini()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Gemini is fully operational!")
    else:
        print("⚠️ Gemini needs attention - check the errors above")
    sys.exit(0 if success else 1)
