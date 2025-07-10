#!/usr/bin/env python3
"""
Quick Gemini connection test
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_gemini_quick():
    """Quick test of Gemini setup"""
    print("🔍 Quick Gemini Test")
    print("=" * 30)
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ No GEMINI_API_KEY found in environment")
        return False
    
    if not api_key.startswith('AIza'):
        print("❌ Invalid API key format (should start with 'AIza')")
        return False
    
    print(f"✅ API key format valid: {api_key[:10]}...")
    
    # Test import
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI library imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test configuration
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini configured successfully")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    # Test model creation
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model created successfully")
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Test basic generation
    try:
        response = model.generate_content("Hello")
        if response and response.text:
            print(f"✅ Response received: {response.text[:50]}...")
            return True
        else:
            print("❌ Empty response")
            return False
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_quick()
    if success:
        print("\n🎉 Gemini is working correctly!")
    else:
        print("\n⚠️ Gemini needs attention")
    sys.exit(0 if success else 1)
