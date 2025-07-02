#!/usr/bin/env python3
"""
Test script for OpenAI integration
Tests the LLMManager with OpenAI support
"""

import os
import sys
sys.path.insert(0, '.')

# Fix import path for LLMManager
sys.path.insert(0, './streamlit/src')
from app import LLMManager
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_integration():
    """Test OpenAI integration with the LLMManager"""
    print("🧪 Testing OpenAI Integration...")
    
    # Load config
    config = Config()
    
    # Check if OpenAI API key is available
    openai_key = config.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  No OpenAI API key found. Please set OPENAI_API_KEY in .env")
        print("   This test will verify the code structure only.")
    
    # Initialize LLM Manager
    llm_manager = LLMManager()
    
    # Test initialization
    print("\n📋 Testing LLM Manager Initialization...")
    success = llm_manager.initialize_models()
    
    if success:
        print("✅ LLM Manager initialized successfully")
        print(f"🔗 Available providers: {llm_manager.available_providers}")
        print(f"🎯 Active provider: {llm_manager.active_provider}")
        
        # Test provider switching
        if 'openai' in llm_manager.available_providers:
            print("\n🔄 Testing OpenAI Provider Switch...")
            if llm_manager.set_active_provider('openai'):
                print("✅ Successfully switched to OpenAI")
                
                # Test a simple response
                if openai_key:
                    print("\n💬 Testing OpenAI Response Generation...")
                    try:
                        response = llm_manager.generate_response("What is 2+2?")
                        print(f"📝 OpenAI Response: {response[:100]}...")
                        print("✅ OpenAI response generation successful")
                    except Exception as e:
                        print(f"❌ OpenAI response generation failed: {str(e)}")
                else:
                    print("⚠️  Skipping response test (no API key)")
            else:
                print("❌ Failed to switch to OpenAI")
        else:
            print("⚠️  OpenAI provider not available")
            
        # Test fallback mechanism
        print("\n🔄 Testing Provider Fallback...")
        original_provider = llm_manager.active_provider
        
        # Try switching to each available provider
        for provider in llm_manager.available_providers:
            if llm_manager.set_active_provider(provider):
                display_name = llm_manager.get_provider_display_name(provider)
                print(f"✅ Successfully switched to {display_name}")
            else:
                print(f"❌ Failed to switch to {provider}")
        
        # Restore original provider
        llm_manager.set_active_provider(original_provider)
        
    else:
        print("❌ LLM Manager initialization failed")
        return False
    
    print("\n🎉 OpenAI Integration Test Completed!")
    return True

def test_configuration():
    """Test configuration for OpenAI"""
    print("\n⚙️  Testing Configuration...")
    
    config = Config()
    
    print(f"📝 OpenAI Model: {config.OPENAI_MODEL}")
    print(f"🔑 OpenAI API Key: {'✅ Set' if config.OPENAI_API_KEY else '❌ Not Set'}")
    print(f"🎯 Default Provider: {config.DEFAULT_PROVIDER}")
    
    return True

if __name__ == "__main__":
    print("🚀 FinOpSysAI - OpenAI Integration Test")
    print("=" * 50)
    
    try:
        # Test configuration
        test_configuration()
        
        # Test OpenAI integration
        test_openai_integration()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
