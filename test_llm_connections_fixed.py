#!/usr/bin/env python3
"""
Test LLM connections and identify specific issues
"""

import sys
import os
import logging
import time
import threading
import concurrent.futures
from typing import Dict, List

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

def test_openai_connection() -> Dict:
    """Test OpenAI API connection"""
    result = {
        'provider': 'OpenAI',
        'success': False,
        'error': None,
        'details': {}
    }
    
    if not config.OPENAI_API_KEY:
        result['error'] = 'No API key provided'
        return result
    
    try:
        import openai
        logger.info("🔄 Testing OpenAI connection...")
        
        # Validate API key format
        if not config.OPENAI_API_KEY.startswith('sk-'):
            result['error'] = 'Invalid API key format'
            return result
        
        # Create client
        client = openai.OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=2,
            base_url="https://api.openai.com/v1"
        )
        
        # Test connection
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0
        )
        end_time = time.time()
        
        if response and response.choices and response.choices[0].message:
            result['success'] = True
            result['details'] = {
                'response_time': f"{end_time - start_time:.2f}s",
                'model_used': "gpt-3.5-turbo",
                'response_content': response.choices[0].message.content
            }
        else:
            result['error'] = 'Empty response from API'
            
    except ImportError:
        result['error'] = 'OpenAI library not installed'
    except Exception as e:
        error_str = str(e).lower()
        if 'authentication' in error_str or 'unauthorized' in error_str:
            result['error'] = 'Authentication failed - check API key'
        elif 'rate limit' in error_str or 'quota' in error_str:
            result['error'] = 'Rate limit/quota exceeded'
        elif 'connection' in error_str or 'network' in error_str or 'dns' in error_str:
            result['error'] = f'Network connectivity issue: {str(e)}'
        else:
            result['error'] = f'Unexpected error: {str(e)}'
    
    return result

def test_gemini_connection() -> Dict:
    """Test Google Gemini API connection"""
    result = {
        'provider': 'Gemini',
        'success': False,
        'error': None,
        'details': {}
    }
    
    if not config.GEMINI_API_KEY:
        result['error'] = 'No API key provided'
        return result
    
    try:
        import google.generativeai as genai
        logger.info("🔄 Testing Gemini connection...")
        
        # Validate API key format
        if not config.GEMINI_API_KEY.startswith('AIza'):
            result['error'] = 'Invalid API key format'
            return result
        
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Create model with safety settings
        generation_config = {
            "temperature": 0.1,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 10,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Test connection with timeout
        start_time = time.time()
        
        # Use concurrent futures for better timeout handling
        def make_request():
            try:
                return model.generate_content("Hi")
            except Exception as e:
                logger.error(f"Gemini request error: {str(e)}")
                raise e
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(make_request)
                response = future.result(timeout=20)  # 20 second timeout
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Request timed out")
            
        end_time = time.time()
        
        if response and response.text:
            result['success'] = True
            result['details'] = {
                'response_time': f"{end_time - start_time:.2f}s",
                'model_used': "gemini-1.5-flash",
                'response_content': response.text
            }
        else:
            result['error'] = 'Empty response from API'
            
    except ImportError:
        result['error'] = 'Google Generative AI library not installed'
    except TimeoutError:
        result['error'] = 'Connection timeout - network issue'
    except KeyboardInterrupt:
        result['error'] = 'Test interrupted - likely connection timeout'
    except Exception as e:
        error_str = str(e).lower()
        error_type = type(e).__name__
        logger.error(f"Gemini error: {error_type}: {str(e)}")
        
        if 'api_key' in error_str or 'authentication' in error_str or 'invalid' in error_str or '401' in error_str:
            result['error'] = 'Authentication failed - check API key'
        elif 'quota' in error_str or 'rate' in error_str or '429' in error_str:
            result['error'] = 'Quota/rate limit exceeded'
        elif 'blocked' in error_str or 'safety' in error_str or 'harm' in error_str:
            result['error'] = 'Safety filter blocked request'
        elif 'connection' in error_str or 'network' in error_str or 'timeout' in error_str or 'dns' in error_str:
            result['error'] = f'Network connectivity issue: {str(e)}'
        elif '403' in error_str or 'forbidden' in error_str:
            result['error'] = 'Access forbidden - check API key permissions'
        elif '500' in error_str or 'internal' in error_str:
            result['error'] = 'Gemini service error - try again later'
        elif 'grpc' in error_str or 'unavailable' in error_str:
            result['error'] = 'Gemini service unavailable - network or service issue'
        else:
            result['error'] = f'Unexpected error ({error_type}): {str(e)}'
    
    return result

def test_ollama_connection() -> Dict:
    """Test Ollama local connection"""
    result = {
        'provider': 'Ollama',
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        import ollama
        logger.info("🔄 Testing Ollama connection...")
        
        # Create client
        client = ollama.Client(host=config.OLLAMA_URL)
        
        # Check if service is available
        models = client.list()
        logger.info(f"🔍 Ollama models available: {len(models.get('models', []))}")
        
        # Test with configured model
        start_time = time.time()
        response = client.chat(
            model=config.OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': 'Hi'}]
        )
        end_time = time.time()
        
        if response and 'message' in response and response['message'].get('content'):
            result['success'] = True
            result['details'] = {
                'response_time': f"{end_time - start_time:.2f}s",
                'model_used': config.OLLAMA_MODEL,
                'response_content': response['message']['content'],
                'service_url': config.OLLAMA_URL,
                'models_available': len(models.get('models', []))
            }
        else:
            result['error'] = f'Model {config.OLLAMA_MODEL} not responding properly'
            
    except ImportError:
        result['error'] = 'Ollama library not installed'
    except Exception as e:
        error_str = str(e).lower()
        if 'connection' in error_str or 'refused' in error_str:
            result['error'] = f'Connection failed - is Ollama running at {config.OLLAMA_URL}?'
        elif 'timeout' in error_str:
            result['error'] = f'Connection timeout at {config.OLLAMA_URL}'
        elif 'not found' in error_str:
            result['error'] = f'Model {config.OLLAMA_MODEL} not found - please pull the model first'
        else:
            result['error'] = f'Unexpected error: {str(e)}'
    
    return result

def main():
    """Run comprehensive LLM connection tests"""
    print("🔍 FinOpSysAI LLM Connection Test")
    print("=" * 50)
    
    # Test all providers
    providers = [
        test_openai_connection,
        test_gemini_connection,
        test_ollama_connection
    ]
    
    results = []
    for test_func in providers:
        result = test_func()
        results.append(result)
        
        # Print result
        if result['success']:
            print(f"✅ {result['provider']}: Connection successful")
            if result['details']:
                for key, value in result['details'].items():
                    print(f"   • {key}: {value}")
        else:
            print(f"❌ {result['provider']}: {result['error']}")
        print()
    
    # Summary
    successful_providers = [r['provider'] for r in results if r['success']]
    failed_providers = [r['provider'] for r in results if not r['success']]
    
    print("📊 SUMMARY")
    print("-" * 20)
    print(f"✅ Working providers: {', '.join(successful_providers) if successful_providers else 'None'}")
    print(f"❌ Failed providers: {', '.join(failed_providers) if failed_providers else 'None'}")
    
    if not successful_providers:
        print("\n⚠️  WARNING: No LLM providers are working!")
        print("The application will run in offline mode.")
    
    print(f"\n🎯 Default provider: {config.DEFAULT_PROVIDER}")
    print(f"🎯 Default model: {config.DEFAULT_MODEL}")

if __name__ == "__main__":
    main()
