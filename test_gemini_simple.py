#!/usr/bin/env python3
"""
Simple Gemini test
"""

import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from config import Config

# Load configuration
config = Config()

def test_gemini_simple():
    """Simple Gemini test"""
    print("🔍 Testing Gemini connection...")
    
    if not config.GEMINI_API_KEY:
        print("❌ No API key provided")
        return
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI library imported")
        
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        print("✅ Gemini configured")
        
        # Create simple model
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model created")
        
        # Test basic connection
        start_time = time.time()
        response = model.generate_content("Hi")
        end_time = time.time()
        
        if response and response.text:
            print(f"✅ Gemini test successful!")
            print(f"   • Response time: {end_time - start_time:.2f}s")
            print(f"   • Response: {response.text}")
        else:
            print("❌ Empty response")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_gemini_simple()
