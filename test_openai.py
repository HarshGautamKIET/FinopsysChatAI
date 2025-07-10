import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import openai
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    print("✅ OpenAI library imported successfully")
    print(f"✅ API key loaded (length: {len(api_key)} characters)")
    
    # Test OpenAI connection
    client = openai.OpenAI(api_key=api_key)
    
    print("🔍 Testing OpenAI API connection...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello! Please respond with just 'OpenAI connection successful'"}],
        max_tokens=10
    )
    
    if response and response.choices:
        result = response.choices[0].message.content
        print(f"✅ OpenAI API test successful: {result}")
    else:
        print("❌ OpenAI API test failed: No response")
        
except ImportError as e:
    print(f"❌ Failed to import OpenAI library: {e}")
except Exception as e:
    print(f"❌ OpenAI API test failed: {e}")
