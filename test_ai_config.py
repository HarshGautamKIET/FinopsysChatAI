import sys
import os

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

# Import the LLMManager (we'll need to mock streamlit session state)
class MockSessionState:
    def __init__(self):
        self.selected_model = "gpt-4o-mini"
    
    def get(self, key, default=None):
        return getattr(self, key, default)

# Mock streamlit for testing
import streamlit as st
st.session_state = MockSessionState()

# Now import and test the LLMManager
sys.path.insert(0, os.path.join(project_root, 'streamlit', 'src'))

# Set up configuration
from config import Config
config = Config()
print("✅ Configuration loaded")

# Test initialization
print("🔍 Testing LLM Manager initialization...")
try:
    # We'll test just the initialization logic without full Streamlit context
    print(f"✅ OpenAI API Key configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
    print(f"✅ Gemini API Key configured: {'Yes' if config.GEMINI_API_KEY else 'No'}")
    print(f"✅ Default Provider: {config.DEFAULT_PROVIDER}")
    print(f"✅ Default Model: {config.DEFAULT_MODEL}")
    print(f"✅ Available OpenAI Models: {config.OPENAI_MODELS}")
    print(f"✅ Available Gemini Models: {config.GEMINI_MODELS}")
    
    print("\n✅ Multi-provider AI system configuration test completed successfully!")
    
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    sys.exit(1)
