#!/usr/bin/env python3
"""
Enhanced Multi-Provider LLM Test
Tests all three providers: Gemini, OpenAI, and Ollama
"""

import os
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './streamlit/src')

from app import LLMManager
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_providers():
    """Test all available LLM providers"""
    print("🚀 FinOpSysAI - Multi-Provider LLM Test")
    print("=" * 50)
    
    # Initialize config
    config = Config()
    
    print("⚙️  Testing Configuration...")
    print(f"📝 Gemini Model: {config.DEFAULT_MODEL}")
    print(f"📝 OpenAI Model: {config.OPENAI_MODEL}")
    print(f"📝 Ollama Model: {config.OLLAMA_MODEL}")
    print(f"🔑 Gemini API Key: {'✅ Set' if config.GEMINI_API_KEY else '❌ Not Set'}")
    print(f"🔑 OpenAI API Key: {'✅ Set' if config.OPENAI_API_KEY else '❌ Not Set'}")
    print(f"🎯 Default Provider: {config.DEFAULT_PROVIDER}")
    
    print("\n🧪 Testing Multi-Provider Integration...")
    
    # Initialize LLM Manager
    llm_manager = LLMManager()
    
    print("📋 Testing LLM Manager Initialization...")
    success = llm_manager.initialize_models()
    
    if success:
        print("✅ LLM Manager initialized successfully")
        print(f"🔗 Available providers: {llm_manager.available_providers}")
        print(f"🎯 Active provider: {llm_manager.active_provider}")
        
        # Test each available provider
        for provider in llm_manager.available_providers:
            print(f"\n🔄 Testing {provider.upper()} Provider...")
            
            # Switch to provider
            if llm_manager.set_active_provider(provider):
                display_name = llm_manager.get_provider_display_name(provider)
                print(f"✅ Successfully switched to {display_name}")
                
                # Test response generation
                try:
                    response = llm_manager.generate_response("What is 2+2? Answer briefly.")
                    if response and not response.startswith("❌"):
                        print(f"📝 {provider.upper()} Response: {response[:100]}...")
                        print(f"✅ {provider.upper()} response generation successful")
                    else:
                        print(f"❌ {provider.upper()} response generation failed")
                except Exception as e:
                    print(f"❌ {provider.upper()} test failed: {str(e)}")
            else:
                print(f"❌ Failed to switch to {provider}")
        
        print("\n🔄 Testing Provider Switching...")
        # Test switching between providers
        for provider in llm_manager.available_providers:
            if llm_manager.set_active_provider(provider):
                display_name = llm_manager.get_provider_display_name(provider)
                print(f"✅ Successfully switched to {display_name}")
        
        print("\n🎉 Multi-Provider LLM Test Completed!")
        print("✅ All tests completed successfully!")
        
        # Display summary
        print("\n📊 Test Summary:")
        print(f"   🔗 Available Providers: {len(llm_manager.available_providers)}")
        for provider in llm_manager.available_providers:
            display_name = llm_manager.get_provider_display_name(provider)
            print(f"   - {display_name}")
        
    else:
        print("❌ LLM Manager initialization failed")
        print("⚠️  Please check your API keys and network connectivity")

if __name__ == "__main__":
    test_all_providers()
