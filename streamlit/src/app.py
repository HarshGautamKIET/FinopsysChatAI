"""
FinOpSysAI - Financial Data Assistant
Streamlit Implementation

FinOpSysAI is Finopsys' financial data assistant designed to help you analyze your invoice data.

Features:
- Gemini AI with Ollama DeepSeek fallback
- Vendor-specific context management
- Strict vendor_id filtering for all queries
- Session-persistent vendor context
"""

import streamlit as st
import logging
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import hashlib
from functools import lru_cache
import sys
import os
import time
from collections import defaultdict, deque
import secrets
import io

# Visualization imports removed - feature no longer supported

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

from config import Config
from utils.query_validator import QueryValidator
from utils.error_handler import error_handler, AppError
from utils.query_optimizer import QueryOptimizer
from utils.delimited_field_processor import delimited_processor
from column_reference_loader import ColumnReferenceLoader
from llm_response_restrictions import response_restrictions
from column_keywords_mapping import column_keywords

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variables
config = Config()
POSTGRES_CONFIG = {
    'host': config.POSTGRES_HOST,
    'port': config.POSTGRES_PORT,
    'user': config.POSTGRES_USER,
    'password': config.POSTGRES_PASSWORD or os.getenv('POSTGRES_PASSWORD'),
    'database': config.POSTGRES_DATABASE,
    'options': f'-c search_path={config.POSTGRES_SCHEMA}'
}

# Use configuration for API keys
OPENAI_API_KEY = config.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = config.GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
TARGET_TABLE = "AI_INVOICE"

class RateLimiter:
    """Rate limiting for API calls and database queries"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True
        return False

class SecurityManager:
    """Enhanced security management"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def check_session_timeout():
        """Check if session has expired"""
        if 'login_time' in st.session_state:
            session_duration = datetime.now() - st.session_state.login_time
            if session_duration > timedelta(hours=1):  # 1 hour timeout
                st.session_state.clear()
                st.error("Session expired. Please login again.")
                st.stop()
    
    @staticmethod
    def log_security_event(event_type: str, details: dict):
        """Log security-related events"""
        logger.warning(f"SECURITY_EVENT: {event_type} - {details}")

# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 requests per minute

class LLMManager:
    """Manages LLM model initialization with fallback mechanism"""
    def __init__(self):
        self.openai_model = None
        self.gemini_model = None
        self.ollama_model = None
        self.active_provider = None
        self.available_providers = []
        self.column_reference = ColumnReferenceLoader()
        self.column_keywords = column_keywords
        
    def initialize_models(self) -> bool:
        """Initialize LLM models with comprehensive error handling and robust connections"""
        success = False
        initialization_errors = []
        
        logger.info("🚀 Starting comprehensive LLM model initialization...")
        
        # Initialize OpenAI with robust error handling
        success |= self._initialize_openai(initialization_errors)
        
        # Initialize Gemini with enhanced connection handling
        success |= self._initialize_gemini(initialization_errors)
        
        # Initialize Ollama with local fallback
        success |= self._initialize_ollama(initialization_errors)
        
        # Handle initialization results
        if not success and not self.available_providers:
            logger.error("❌ No LLM models available - running in offline mode")
            logger.info("🔍 Initialization Summary:")
            for error in initialization_errors:
                logger.info(f"   • {error}")
            self.available_providers.append("offline")
            self.active_provider = "offline"
            self.initialization_errors = initialization_errors
        
        # Log final status
        logger.info(f"🔄 Available providers: {self.available_providers}")
        logger.info(f"🎯 Active provider: {self.active_provider}")
        
        return success or len(self.available_providers) > 0
    
    def _initialize_openai(self, initialization_errors: list) -> bool:
        """Initialize OpenAI with comprehensive error handling"""
        if not OPENAI_API_KEY or len(OPENAI_API_KEY.strip()) == 0:
            error_msg = "No OpenAI API key provided"
            logger.warning(f"⚠️ {error_msg}")
            initialization_errors.append(f"OpenAI: {error_msg}")
            return False
        
        try:
            import openai
            logger.info("🔄 Attempting OpenAI initialization...")
            
            # Validate API key format
            if not OPENAI_API_KEY.startswith('sk-'):
                error_msg = "Invalid OpenAI API key format"
                logger.error(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: {error_msg}")
                return False
            
            # Create client with robust configuration
            client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=30.0,
                max_retries=2,
                base_url="https://api.openai.com/v1"  # Explicit base URL
            )
            
            # Test connection with minimal request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0
            )
            
            if response and response.choices and response.choices[0].message:
                self.openai_model = client
                self.available_providers.append("openai")
                if not self.active_provider:
                    self.active_provider = "openai"
                logger.info("✅ OpenAI API initialized successfully")
                return True
            else:
                error_msg = "OpenAI test call returned empty response"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: {error_msg}")
                return False
                
        except ImportError:
            error_msg = "OpenAI library not installed - run: pip install openai"
            logger.warning(f"❌ {error_msg}")
            initialization_errors.append(f"OpenAI: {error_msg}")
            return False
        except Exception as e:
            error_str = str(e).lower()
            if 'authentication' in error_str or 'unauthorized' in error_str:
                error_msg = "OpenAI authentication failed - check your API key"
                logger.error(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: Invalid API key")
            elif 'rate limit' in error_str or 'quota' in error_str:
                error_msg = "OpenAI rate limit/quota exceeded"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: Rate limit exceeded")
            elif 'connection' in error_str or 'network' in error_str or 'dns' in error_str:
                error_msg = f"OpenAI connection failed - network issue: {str(e)}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: Network connectivity issue")
            else:
                error_msg = f"OpenAI initialization failed: {str(e)}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"OpenAI: {str(e)}")
            return False
    
    def _initialize_gemini(self, initialization_errors: list) -> bool:
        """Initialize Gemini with enhanced connection handling"""
        if not GEMINI_API_KEY or len(GEMINI_API_KEY.strip()) == 0:
            error_msg = "No Gemini API key provided"
            logger.warning(f"⚠️ {error_msg}")
            initialization_errors.append(f"Gemini: {error_msg}")
            return False
        
        try:
            import google.generativeai as genai
            logger.info("🔄 Attempting Gemini initialization...")
            
            # Validate API key format
            if not GEMINI_API_KEY.startswith('AIza'):
                error_msg = "Invalid Gemini API key format"
                logger.error(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: {error_msg}")
                return False
            
            # Configure Gemini
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Create model with safety settings
            generation_config = {
                "temperature": 0.3,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 100,
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
                },
            ]
            
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Test connection with timeout using concurrent futures
            import concurrent.futures
            
            def test_gemini():
                return model.generate_content("Hi")
            
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(test_gemini)
                    response = future.result(timeout=20)  # 20 second timeout
            except concurrent.futures.TimeoutError:
                error_msg = "Gemini connection timeout - network issue"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: Connection timeout")
                return False
            
            if response and response.text:
                self.gemini_model = model
                self.available_providers.append("gemini")
                if not self.active_provider:
                    self.active_provider = "gemini"
                logger.info("✅ Gemini AI initialized successfully")
                return True
            else:
                error_msg = "Gemini test call returned empty response"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: {error_msg}")
                return False
                
        except ImportError:
            error_msg = "Google Generative AI library not installed - run: pip install google-generativeai"
            logger.warning(f"❌ {error_msg}")
            initialization_errors.append(f"Gemini: {error_msg}")
            return False
        except Exception as e:
            error_str = str(e).lower()
            if 'api_key' in error_str or 'authentication' in error_str or 'invalid' in error_str:
                error_msg = "Gemini authentication failed - check your API key"
                logger.error(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: Invalid API key")
            elif 'quota' in error_str or 'rate' in error_str:
                error_msg = "Gemini quota/rate limit exceeded"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: Rate limit exceeded")
            elif 'blocked' in error_str or 'safety' in error_str:
                error_msg = "Gemini safety filter blocked request"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: Safety filter issue")
            elif 'connection' in error_str or 'network' in error_str or 'timeout' in error_str:
                error_msg = f"Gemini connection failed - network issue: {str(e)}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: Network connectivity issue")
            else:
                error_msg = f"Gemini initialization failed: {str(e)}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Gemini: {str(e)}")
            return False
    
    def _initialize_ollama(self, initialization_errors: list) -> bool:
        """Initialize Ollama with local connection handling"""
        try:
            import ollama
            logger.info("🔄 Attempting Ollama initialization...")
            
            # Test Ollama connection with timeout
            client = ollama.Client(host=config.OLLAMA_URL)
            
            # Simple test to check if Ollama is running
            try:
                # First check if Ollama service is available
                models = client.list()
                logger.info(f"🔍 Ollama models available: {len(models.get('models', []))}")
                
                # Test with the configured model
                response = client.chat(
                    model=config.OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': 'Hi'}]
                )
                
                if response and 'message' in response and response['message'].get('content'):
                    self.ollama_model = {
                        'client': client,
                        'model': config.OLLAMA_MODEL
                    }
                    self.available_providers.append("ollama")
                    if not self.active_provider:
                        self.active_provider = "ollama"
                    logger.info(f"✅ Ollama ({config.OLLAMA_MODEL}) initialized successfully")
                    return True
                else:
                    error_msg = f"Ollama model {config.OLLAMA_MODEL} not responding properly"
                    logger.warning(f"❌ {error_msg}")
                    initialization_errors.append(f"Ollama: {error_msg}")
                    return False
                    
            except Exception as model_error:
                if 'not found' in str(model_error).lower():
                    error_msg = f"Ollama model {config.OLLAMA_MODEL} not found - please pull the model first"
                    logger.warning(f"❌ {error_msg}")
                    initialization_errors.append(f"Ollama: Model not found")
                else:
                    raise model_error
                    
        except ImportError:
            error_msg = "Ollama library not installed - run: pip install ollama"
            logger.warning(f"❌ {error_msg}")
            initialization_errors.append(f"Ollama: {error_msg}")
            return False
        except Exception as e:
            error_str = str(e).lower()
            if 'connection' in error_str or 'refused' in error_str:
                error_msg = f"Ollama connection failed - is Ollama running at {config.OLLAMA_URL}?"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Ollama: Service not running")
            elif 'timeout' in error_str:
                error_msg = f"Ollama connection timeout at {config.OLLAMA_URL}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Ollama: Connection timeout")
            else:
                error_msg = f"Ollama initialization failed: {str(e)}"
                logger.warning(f"❌ {error_msg}")
                initialization_errors.append(f"Ollama: {str(e)}")
            return False
    
    def set_active_provider(self, provider: str) -> bool:
        """Set active provider if available"""
        if provider in self.available_providers:
            self.active_provider = provider
            logger.info(f"🔄 Switched to {provider.upper()} provider")
            return True
        return False
    
    def get_available_models(self, provider: str) -> list:
        """Get available models for a provider"""
        if provider == "openai":
            return [
                "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", 
                "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
            ]
        elif provider == "gemini":
            return [
                "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"
            ]
        elif provider == "ollama":
            return [config.OLLAMA_MODEL]
        return []
    
    def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate response using active model with fallback"""
        # Check rate limiting
        client_id = st.session_state.get('session_id', 'anonymous')
        if not rate_limiter.is_allowed(client_id):
            return "❌ Rate limit exceeded. Please wait before making another request."
        
        # Handle offline mode
        if self.active_provider == "offline":
            return self._generate_offline_response(prompt)
        
        try:
            if self.active_provider == "openai" and self.openai_model:
                # Use selected model from session state or default
                model_name = model or getattr(st.session_state, 'selected_model', config.DEFAULT_MODEL)
                if not model_name.startswith('gpt'):
                    model_name = "gpt-4o-mini"
                    
                response = self.openai_model.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3,
                    timeout=30.0
                )
                return response.choices[0].message.content if response.choices else "No response generated"
                
            elif self.active_provider == "gemini" and self.gemini_model:
                # Use selected model from session state or default
                model_name = model or getattr(st.session_state, 'selected_model', 'gemini-1.5-flash')
                # Ensure we have a valid Gemini model name
                if not model_name.startswith('gemini'):
                    model_name = "gemini-1.5-flash"
                # Create model instance with selected model
                if model_name != getattr(self.gemini_model, '_model_name', 'gemini-1.5-flash'):
                    import google.generativeai as genai
                    self.gemini_model = genai.GenerativeModel(model_name)
                response = self.gemini_model.generate_content(prompt)
                return response.text if response and response.text else "No response generated"
                
            elif self.active_provider == "ollama" and self.ollama_model:
                response = self.ollama_model['client'].chat(
                    model=self.ollama_model['model'],
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response['message']['content'] if response and 'message' in response else "No response generated"
                
        except Exception as e:
            # Handle specific OpenAI errors if available
            error_type = type(e).__name__
            if 'AuthenticationError' in error_type:
                logger.error("❌ OpenAI authentication failed - API key may be invalid")
            elif 'RateLimitError' in error_type:
                logger.warning("❌ OpenAI rate limit exceeded")
            elif 'APIConnectionError' in error_type or 'ConnectionError' in error_type:
                logger.error(f"❌ Connection error: {str(e)}")
            else:
                logger.error(f"❌ Response generation failed with {self.active_provider}: {str(e)}")
            
        # Try fallback providers
        for fallback_provider in self.available_providers:
            if fallback_provider != self.active_provider and fallback_provider != "offline":
                try:
                    old_provider = self.active_provider
                    self.active_provider = fallback_provider
                    logger.info(f"🔄 Trying fallback to {fallback_provider.upper()}")
                    
                    # Use appropriate model for fallback provider
                    fallback_model = None
                    if fallback_provider == "openai":
                        fallback_model = "gpt-4o-mini"
                    elif fallback_provider == "gemini":
                        fallback_model = "gemini-1.5-flash"
                    elif fallback_provider == "ollama":
                        fallback_model = config.OLLAMA_MODEL
                    
                    return self.generate_response(prompt, fallback_model)
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback to {fallback_provider} also failed: {str(fallback_error)}")
                    continue
        
        # Final fallback to offline mode
        logger.warning("🔄 All providers failed, switching to offline mode")
        self.active_provider = "offline"
        return self._generate_offline_response(prompt)
    
    def _generate_offline_response(self, prompt: str) -> str:
        """Generate basic response when no LLM is available"""
        prompt_lower = prompt.lower()
        
        # Basic pattern matching for common queries
        if any(word in prompt_lower for word in ['total', 'sum', 'amount']):
            return ("💰 **Financial Analysis:** I can help you analyze financial data, but LLM services are currently unavailable. "
                   "The query results will be displayed below with raw data.")
        
        elif any(word in prompt_lower for word in ['item', 'product', 'service']):
            return ("📦 **Product Analysis:** I can retrieve item-level data, but detailed analysis requires LLM services which are currently unavailable. "
                   "Please check the data table below for product information.")
        
        elif any(word in prompt_lower for word in ['overdue', 'due', 'payment']):
            return ("⏰ **Payment Status:** Payment-related data will be shown below. "
                   "LLM services are unavailable for detailed analysis.")
        
        else:
            return ("🔍 **Data Query:** Your query has been processed and results are shown below. "
                   "Advanced analysis is temporarily unavailable due to connectivity issues. "
                   "Please review the data table for information.")

class PostgreSQLManager:
    """Enhanced PostgreSQL manager with connection pooling and security"""
    
    def __init__(self):
        self.connection = None
        self.vendor_id = None
        self.case_id = None
        self.connection_validated = False
        
    def connect(self) -> bool:
        """Establish PostgreSQL connection with validation"""
        try:
            # Validate configuration first
            config.validate_config()
            
            self.connection = psycopg2.connect(**POSTGRES_CONFIG)
            
            # Test connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0] == 1:
                self.connection_validated = True
                logger.info("✅ PostgreSQL connection established and validated")
                return True
            else:
                logger.error("❌ PostgreSQL connection test failed")
                return False
                
        except ValueError as e:
            logger.error(f"❌ Configuration error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
            return False
    
    def get_available_cases(self) -> list:
        """Get list of available case_ids with error handling"""
        if not self.connection or not self.connection_validated:
            logger.error("❌ No valid database connection")
            return []
        
        try:
            cursor = self.connection.cursor()
            # Use parameterized query for security
            query = f"SELECT DISTINCT case_id FROM {TARGET_TABLE} ORDER BY case_id LIMIT 20"
            cursor.execute(query)
            cases = [row[0] for row in cursor.fetchall()]
            cursor.close()
            logger.info(f"✅ Retrieved {len(cases)} available cases")
            return cases
        except Exception as e:
            logger.error(f"❌ Failed to get case IDs: {str(e)}")
            return []
    
    def set_vendor_context(self, case_id: str) -> bool:
        """Set vendor context with enhanced validation"""
        if not self.connection or not self.connection_validated:
            logger.error("❌ No valid database connection")
            return False
            
        try:
            cursor = self.connection.cursor()
            # Use parameterized query to prevent SQL injection
            query = f"SELECT vendor_id FROM {TARGET_TABLE} WHERE case_id = %s LIMIT 1"
            cursor.execute(query, (case_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self.case_id = case_id
                self.vendor_id = result[0]
                logger.info(f"✅ Vendor context set: case_id={case_id}, vendor_id={self.vendor_id}")
                return True
            else:
                logger.warning(f"⚠️ No vendor found for case_id: {case_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to set vendor context: {str(e)}")
            return False
    
    @error_handler("Database query failed")
    def execute_vendor_query(self, sql_query: str) -> dict:
        """Enhanced query execution with security validation"""
        if not self.vendor_id:
            raise AppError("No vendor context established")
        
        # Use the existing QueryValidator
        validation_result = QueryValidator.validate_query(sql_query, self.vendor_id)
        if not validation_result["valid"]:
            raise AppError(f"Security validation failed: {validation_result['error']}")
        
        # Execute with proper error handling
        try:
            # Reset connection on transaction error
            if self.connection.closed:
                self.connect()
            
            # Reset transaction state if needed
            if self.connection.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                self.connection.rollback()
                
            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchmany(1000)  # Limit results
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            
            result = {
                "success": True,
                "data": results,
                "columns": columns,
                "row_count": len(results)
            }
            
            # Store last query result for data processing
            self.last_query_result = result
            
            return result
        except Exception as e:
            # Reset connection on any error to prevent stuck transactions
            try:
                if self.connection and not self.connection.closed:
                    self.connection.rollback()
            except:
                pass
            raise AppError("Query execution failed", str(e))
    
    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_cached_query_result(query_hash: str, query: str):
        """Cache frequently used queries"""
        return None  # Will be populated by actual query execution
    
    def execute_cached_query(self, sql_query: str) -> dict:
        """Execute query with caching and optimization"""
        # Create query hash for caching
        query_hash = hashlib.md5(f"{sql_query}_{self.vendor_id}".encode()).hexdigest()
        
        # Apply query optimization before execution
        optimized_query = QueryOptimizer.add_performance_hints(sql_query, self.vendor_id)
        optimized_query = QueryOptimizer.optimize_query_structure(optimized_query)
        
        # Get cost estimation for monitoring
        cost_estimate = QueryOptimizer.estimate_query_cost(optimized_query)
        logger.info(f"🔍 Query cost estimate: {cost_estimate['performance_tier']} (Cost: {cost_estimate['estimated_cost']})")
        
        # Try to get cached result (placeholder for now)
        # In production, implement proper caching with Redis or similar
        cached_result = None  # self.get_cached_query_result(query_hash, optimized_query)
        if cached_result:
            logger.info(f"📄 Using cached result for query hash: {query_hash[:8]}...")
            return cached_result
        
        # Execute optimized query
        result = self.execute_vendor_query(optimized_query)
        
        # Cache successful results (placeholder)
        if result.get("success"):
            logger.info(f"💾 Caching result for query hash: {query_hash[:8]}...")
            # self.cache_query_result(query_hash, result)
        
        return result

class ContextAwareChat:
    """Main chat application with context management"""
    def __init__(self):
        self.llm_manager = LLMManager()
        self.db_manager = PostgreSQLManager()
        self.delimited_processor = delimited_processor
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize both LLM and database connections"""
        llm_success = self.llm_manager.initialize_models()
        db_success = self.db_manager.connect()
        self.initialized = llm_success and db_success
        return self.initialized
    
    def limit_data_for_llm(self, result: dict, max_rows: int = 50) -> dict:
        """Limit the amount of data sent to LLM to prevent context length issues"""
        if not result.get("success") or not result.get("data"):
            return result
        
        # If data is within limit, return as is
        if len(result["data"]) <= max_rows:
            return result
        
        # Create a limited version for LLM
        limited_result = result.copy()
        limited_result["data"] = result["data"][:max_rows]
        limited_result["truncated"] = True
        limited_result["original_row_count"] = len(result["data"])
        limited_result["displayed_row_count"] = max_rows
        
        return limited_result
    
    def generate_sql_query(self, user_question: str) -> str:
        """Generate SQL query with vendor context and delimited field awareness"""
        if not self.db_manager.vendor_id:
            return "❌ Error: No vendor context established."
        
        # ALWAYS use cached analysis when available - this prevents duplicate analysis
        if hasattr(self, '_cached_query_analysis') and self._cached_query_analysis.get('question') == user_question:
            is_item_query = self._cached_query_analysis['is_item_query']
            is_specific_product_query = self._cached_query_analysis['is_specific_product_query']
            extracted_products = self._cached_query_analysis['extracted_products']
        else:
            # Fallback: perform fresh analysis only if cache is not available
            logger.warning("⚠️ No cached query analysis available, performing fresh analysis")
            is_item_query = self.delimited_processor.is_item_query(user_question)
            is_specific_product_query = self.delimited_processor.is_specific_product_query(user_question)
            extracted_products = self.delimited_processor.extract_product_names_from_query(user_question)
        
        # If this is a specific product query, generate targeted SQL
        if is_specific_product_query and extracted_products:
            sql_query = self.delimited_processor.generate_product_specific_sql(
                user_question, self.db_manager.vendor_id, extracted_products
            )
            if sql_query:
                logger.info(f"🔍 Generated product-specific SQL: {sql_query}")
                return sql_query
        
        # Get enhanced prompt context with comprehensive column mappings
        enhanced_context = self.llm_manager.column_keywords.get_enhanced_prompt_context(
            self.db_manager.vendor_id, 
            self.db_manager.case_id
        )
        
        # Add specific guidance for item queries
        if is_item_query or is_specific_product_query:
            enhanced_context += f"""

ITEM-LEVEL QUERY DETECTED:
For questions about items, products, or services, ALWAYS include these columns:
- ITEMS_DESCRIPTION (contains product/service names in JSON arrays)
- ITEMS_UNIT_PRICE (contains prices per item in JSON arrays)
- ITEMS_QUANTITY (contains quantities per item in JSON arrays)

IMPORTANT: These columns contain JSON arrays like ["Cloud Storage", "Support"] and [99.99, 150.00].
For specific product searches, use LIKE operators: WHERE LOWER(ITEMS_DESCRIPTION) LIKE LOWER('%product_name%')

Example for item queries:
SELECT case_id, bill_date, items_description, items_unit_price, items_quantity 
FROM AI_INVOICE WHERE vendor_id = '{self.db_manager.vendor_id}'
ORDER BY bill_date DESC"""
        
        prompt = f"""{enhanced_context}

USER QUESTION: {user_question}

Generate ONLY a valid SQL query for PostgreSQL database. Follow these strict requirements:
1. ALWAYS include: WHERE vendor_id = '{self.db_manager.vendor_id}'
2. Use ONLY the AI_INVOICE table
3. Return ONLY the SQL query - no explanations, no markdown, no extra text
4. Map user keywords to correct column names using the comprehensive guide above
5. For item-related queries, include ITEMS_* columns for detailed breakdowns
6. For specific product searches, use LIKE operators on ITEMS_DESCRIPTION

SQL QUERY:"""
        
        sql_query = self.llm_manager.generate_response(prompt, getattr(st.session_state, 'selected_model', None))
        
        # Clean up the response to extract just the SQL
        sql_query = sql_query.strip()
          # Remove common prefixes/suffixes that LLMs might add
        for prefix in ["```sql", "```", "SQL:", "Query:", "Answer:"]:
            if sql_query.upper().startswith(prefix.upper()):
                sql_query = sql_query[len(prefix):].strip()
        
        for suffix in ["```", ";"]:
            if sql_query.endswith(suffix):
                sql_query = sql_query[:-len(suffix)].strip()
        
        # Ensure the query includes vendor filtering
        if "vendor_id" not in sql_query.lower():
            if "where" in sql_query.lower():
                sql_query += f" AND vendor_id = '{self.db_manager.vendor_id}'"
            else:
                sql_query += f" WHERE vendor_id = '{self.db_manager.vendor_id}'"
        
        logger.info(f"🔍 Generated SQL: {sql_query}")
        return sql_query
    
    def process_user_query(self, user_question: str) -> str:
        """Process user query with vendor context and automatic intelligent item handling"""
        if not self.initialized:
            return "❌ System not initialized. Please contact administrator."
        
        if not self.db_manager.vendor_id:
            return "❌ No vendor context established. Please select a case ID first."
        
        try:
            # Check if we already processed this exact query recently to prevent duplicates
            # Use session state for persistence across Streamlit reruns
            last_processed_query = st.session_state.get('chat_last_processed_query', None)
            last_query_response = st.session_state.get('chat_last_query_response', None)
            
            if last_processed_query == user_question and last_query_response:
                logger.info(f"⚠️ Returning cached response for duplicate query: {user_question}")
                return last_query_response
            
            # Cache the query analysis to avoid multiple calls during same request
            if not hasattr(self, '_cached_query_analysis') or self._cached_query_analysis.get('question') != user_question:
                logger.info(f"🔄 Performing fresh query analysis for: {user_question}")
                self._cached_query_analysis = {
                    'question': user_question,
                    'is_item_query': self.delimited_processor.is_item_query(user_question),
                    'is_specific_product_query': self.delimited_processor.is_specific_product_query(user_question),
                    'extracted_products': self.delimited_processor.extract_product_names_from_query(user_question)
                }
            else:
                logger.info(f"✅ Using cached query analysis for: {user_question}")
            
            # Use cached analysis
            is_item_query = self._cached_query_analysis['is_item_query']
            is_specific_product_query = self._cached_query_analysis['is_specific_product_query']
            extracted_products = self._cached_query_analysis['extracted_products']
            
            # Generate SQL query (enhanced for item detection and specific products)
            sql_query = self.generate_sql_query(user_question)
            
            # Execute query with vendor filtering
            result = self.db_manager.execute_vendor_query(sql_query)
            
            # Store the result for display purposes
            self.db_manager.last_query_result = result
            
            # Always attempt item expansion for item queries or when item columns are present
            processed_result = result
            if result.get("success"):
                # Check if result has item columns (using lowercase column names for PostgreSQL)
                has_item_columns = any(col in ['items_description', 'items_unit_price', 'items_quantity'] 
                                     for col in result.get("columns", []))
                
                if is_item_query or has_item_columns:
                    # Attempt to expand items - this will auto-detect JSON arrays and CSV
                    expanded_result = self.delimited_processor.expand_results_with_items(result)
                    if expanded_result.get('items_expanded'):
                        processed_result = expanded_result
                        self.db_manager.last_query_result = processed_result
                        logger.info(f"✅ Auto-expanded {result.get('data', []).__len__()} invoices to {expanded_result.get('expanded_row_count', 0)} line items")
            
            # Create safe context for LLM response
            safe_context = response_restrictions.create_safe_context_prompt(self.db_manager.vendor_id)
            
            # Limit data for LLM to prevent context length issues
            llm_result = self.limit_data_for_llm(processed_result, max_rows=30)
            
            # Generate natural language response with safety guidelines
            response_prompt = f"""
            {safe_context}
            
            {response_restrictions.get_response_guidelines()}
            
            Based on the following SQL query and result:
            
            Query: {sql_query}
            Result: {llm_result}
            User Question: {user_question}
            
            {"Note: This result was truncated to " + str(llm_result.get('displayed_row_count', 0)) + " rows out of " + str(llm_result.get('original_row_count', 0)) + " total rows for analysis." if llm_result.get('truncated') else ""}
            
            Provide a clear, concise answer to the user's question: {user_question}
            
            Remember: Never include specific ID values, case numbers, or vendor codes in your response.
            Focus on the data insights while maintaining privacy and security.
            
            {"ITEM-LEVEL ANALYSIS: This query involves individual items/products. The data has been automatically expanded to show individual line items. Provide insights about item-level details, quantities, pricing, and totals. Focus on product/service analysis." if processed_result.get('items_expanded') else ""}
            """
            final_response = self.llm_manager.generate_response(response_prompt, getattr(st.session_state, 'selected_model', None))
            
            # Enhanced response formatting for specific product queries and general item queries
            formatted_response = self.format_enhanced_response(final_response, processed_result, user_question, 
                                                               is_specific_product_query, extracted_products, llm_result)
            
            # Filter the response to remove any sensitive information
            filtered_response = response_restrictions.filter_response(formatted_response)
            
            # Cache the response for duplicate prevention in session state
            st.session_state.chat_last_processed_query = user_question
            st.session_state.chat_last_query_response = filtered_response
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {str(e)}")
            error_response = f"❌ Error processing your query: {str(e)}"
            # Cache error response too
            st.session_state.chat_last_processed_query = user_question
            st.session_state.chat_last_query_response = error_response
            return error_response

    def format_enhanced_response(self, raw_response: str, processed_result: dict, user_question: str, 
                               is_specific_product_query: bool, extracted_products: list, llm_result: dict) -> str:
        """Enhanced response formatting with improved structure, emojis, and visual hierarchy"""
        
        # Start with formatted sections
        response_sections = []
        
        # Add query summary header
        query_summary = self._create_query_summary(user_question, processed_result)
        if query_summary:
            response_sections.append(query_summary)
        
        # Add data context if available (truncation info)
        if llm_result.get('truncated'):
            response_sections.append(
                f"📊 **Data Summary:** Analyzed {llm_result.get('displayed_row_count', 0)} rows "
                f"out of {llm_result.get('original_row_count', 0)} total results"
            )
        
        # Clean and format the main LLM response
        clean_response = self._clean_llm_response(raw_response)
        
        # Add main response with improved formatting
        if clean_response:
            # Add contextual header based on query type
            if 'total' in user_question.lower() or 'sum' in user_question.lower():
                response_sections.append(f"💰 **Financial Summary:**\n{clean_response}")
            elif 'item' in user_question.lower() or 'product' in user_question.lower():
                response_sections.append(f"📦 **Product Analysis:**\n{clean_response}")
            elif 'overdue' in user_question.lower() or 'due' in user_question.lower():
                response_sections.append(f"⏰ **Payment Status:**\n{clean_response}")
            elif 'trend' in user_question.lower() or 'pattern' in user_question.lower():
                response_sections.append(f"📈 **Trend Analysis:**\n{clean_response}")
            else:
                response_sections.append(f"💡 **Analysis:**\n{clean_response}")
        
        # Add specialized formatting for different query types
        if processed_result.get('items_expanded'):
            if is_specific_product_query and extracted_products:
                # Product-specific insights
                product_summary = self.delimited_processor.format_product_specific_response(
                    processed_result, user_question, extracted_products
                )
                if product_summary and "No information found" not in product_summary:
                    # Enhance product summary with better formatting
                    enhanced_product_summary = self._enhance_product_summary(product_summary, extracted_products)
                    response_sections.append(f"🎯 **Product Details:**\n{enhanced_product_summary}")
            else:
                # General item insights
                item_summary = self.delimited_processor.format_item_response(processed_result, user_question)
                if item_summary and "No detailed item information found" not in item_summary:
                    response_sections.append(f"📦 **Item Breakdown:**\n{item_summary}")
        
        # Add key metrics summary if applicable
        metrics_summary = self._extract_key_metrics(processed_result, user_question)
        if metrics_summary:
            response_sections.append(f"📊 **Key Metrics:**\n{metrics_summary}")
        
        # Add data quality indicators
        data_quality_info = self._get_data_quality_info(processed_result)
        if data_quality_info:
            response_sections.append(f"ℹ️ **Data Insights:**\n{data_quality_info}")
        
        # Combine all sections with proper spacing (removed Next Steps and footer)
        final_response = "\n\n---\n\n".join(response_sections)
        
        return final_response
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean and format the raw LLM response with proper line breaks"""
        if not response:
            return ""
        
        # Remove common LLM artifacts
        response = response.strip()
        
        # Remove redundant phrases
        redundant_phrases = [
            "Based on the query results,",
            "According to the data,",
            "The query shows that",
            "Looking at the results,",
            "From the data provided,",
            "The analysis shows",
            "Here's what I found:",
            "Based on your query:"
        ]
        
        for phrase in redundant_phrases:
            if response.lower().startswith(phrase.lower()):
                response = response[len(phrase):].strip()
        
        # Split into sentences for better formatting
        import re
        
        # Split on periods followed by space and capital letter or end of string
        sentences = re.split(r'\.(?=\s+[A-Z]|$)', response)
        formatted_lines = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add back the period if it was removed by split
            if not sentence.endswith('.') and not sentence.endswith('!') and not sentence.endswith('?'):
                sentence += '.'
            
            # Check for paragraph-starting keywords
            paragraph_starters = [
                'Total', 'However', 'Additionally', 'Furthermore', 'In summary', 
                'Overall', 'The', 'This', 'These', 'Most', 'All', 'Some', 'Each'
            ]
            
            # Format based on content
            if any(sentence.startswith(starter) for starter in paragraph_starters):
                formatted_lines.append(sentence)
                formatted_lines.append("")  # Add blank line for spacing
            elif sentence.startswith('- ') or sentence.startswith('* '):
                # Handle bullet points
                formatted_lines.append(sentence)
            elif re.match(r'^\d+[\.)]\s', sentence):
                # Handle numbered lists
                formatted_lines.append(sentence)
            else:
                # Regular sentence
                formatted_lines.append(sentence)
                formatted_lines.append("")  # Add spacing after each sentence
        
        # Remove extra blank lines at the end
        while formatted_lines and formatted_lines[-1] == "":
            formatted_lines.pop()
        
        # Join with newlines for proper formatting
        formatted_text = '\n'.join(formatted_lines)
        
        # Add emphasis to important terms
        important_terms = ['overdue', 'unpaid', 'balance', 'due', 'paid', 'outstanding']
        for term in important_terms:
            formatted_text = re.sub(
                rf'\b{re.escape(term)}\b', 
                f'**{term}**', 
                formatted_text, 
                flags=re.IGNORECASE
            )
        
        # Highlight currency amounts
        formatted_text = re.sub(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', r'**$\1**', formatted_text)
        
        return formatted_text
    
    def _get_data_quality_info(self, processed_result: dict) -> str:
        """Generate concise data quality information"""
        if not processed_result.get('success') or not processed_result.get('data'):
            return ""
        
        row_count = len(processed_result['data'])
        info_parts = []
        
        # Simple data completeness
        if row_count > 0:
            if processed_result.get('items_expanded'):
                original_count = processed_result.get('original_row_count', 0)
                if original_count > 0:
                    info_parts.append(f"**Data Expanded:** {original_count} invoices → {row_count} line items")
            else:
                info_parts.append(f"**Records Analyzed:** {row_count}")
        
        return '\n'.join(info_parts) if info_parts else ""
    
    def _get_response_suggestions(self, user_question: str, processed_result: dict) -> str:
        """Generate helpful suggestions based on the query and results"""
        suggestions = []
        
        # Query-specific suggestions
        question_lower = user_question.lower()
        
        if 'total' in question_lower or 'sum' in question_lower:
            suggestions.append("Try asking about average amounts or trends over time")
            suggestions.append("Ask 'Show me monthly spending patterns' for trend analysis")
        
        if 'overdue' in question_lower or 'due' in question_lower:
            suggestions.append("You can also ask about payment patterns or aging reports")
            suggestions.append("Try 'Which vendor has the most overdue invoices?'")
        
        if 'item' in question_lower or 'product' in question_lower:
            suggestions.append("Ask about specific products by name for detailed analysis")
            suggestions.append("Try 'What's the most expensive item?' or 'Show me recurring services'")
            suggestions.append("Ask 'Find all software-related expenses' for category analysis")
        
        if 'price' in question_lower or 'cost' in question_lower:
            suggestions.append("Compare prices: 'What's the price range for cloud services?'")
            suggestions.append("Ask 'Show me price trends for hosting services'")
        
        # Data-driven suggestions based on results
        if processed_result.get('success') and processed_result.get('data'):
            columns = [c.lower() for c in processed_result.get('columns', [])]
            row_count = len(processed_result['data'])
            
            if 'bill_date' in columns and row_count > 5:
                suggestions.append("Explore trends: 'Show me spending by month' or 'What's my quarterly total?'")
            
            if any('items_' in col for col in columns):
                suggestions.append("Dive deeper: 'What items appear most frequently?' or 'Find my software expenses'")
                suggestions.append("Category analysis: 'Group items by type' or 'Show me service vs product costs'")
            
            if 'balance_amount' in columns:
                suggestions.append("Payment insights: 'What's my average payment time?' or 'Show unpaid balances'")
            
            if row_count > 20:
                suggestions.append("Filter results: 'Show only invoices over $1000' or 'Find recent transactions'")
            
            # Smart suggestions based on data patterns
            if processed_result.get('items_expanded'):
                suggestions.append("Product analysis: 'What's my most common purchase?' or 'Compare vendor pricing'")
        
        # Context-aware suggestions
        if not suggestions:
            suggestions.extend([
                "Ask about spending patterns: 'What's my monthly average?'",
                "Explore vendor relationships: 'Which vendor do I use most?'",
                "Analyze payment behavior: 'How quickly do I pay invoices?'"
            ])
        
        # Limit to top 3 most relevant suggestions
        return '\n'.join([f"  • {s}" for s in suggestions[:3]]) if suggestions else ""

    def _create_query_summary(self, user_question: str, processed_result: dict) -> str:
        """Create a concise summary of what the query is about"""
        if not processed_result.get('success'):
            return ""
        
        row_count = len(processed_result.get('data', []))
        
        # Simple, clean summary without emojis
        return f"**Query Results:** {row_count} records found"
    
    def _classify_query_type(self, user_question: str) -> str:
        """Classify the type of query for better formatting"""
        question_lower = user_question.lower()
        
        financial_keywords = ['total', 'sum', 'amount', 'cost', 'price', 'spend', 'balance']
        product_keywords = ['item', 'product', 'service', 'software', 'hosting', 'cloud']
        temporal_keywords = ['month', 'year', 'trend', 'pattern', 'time', 'date', 'recent']
        status_keywords = ['overdue', 'due', 'paid', 'unpaid', 'status', 'outstanding']
        
        if any(keyword in question_lower for keyword in financial_keywords):
            return 'financial'
        elif any(keyword in question_lower for keyword in product_keywords):
            return 'product'
        elif any(keyword in question_lower for keyword in temporal_keywords):
            return 'temporal'
        elif any(keyword in question_lower for keyword in status_keywords):
            return 'status'
        else:
            return 'general'
    
    def _enhance_product_summary(self, product_summary: str, extracted_products: list) -> str:
        """Enhance product summary with better formatting"""
        if not product_summary:
            return ""
        
        # Add product names as headers if multiple products
        if len(extracted_products) > 1:
            enhanced = f"*Found information for: {', '.join(extracted_products)}*\n\n{product_summary}"
        else:
            enhanced = f"*Product: {extracted_products[0]}*\n\n{product_summary}"
        
        # Format currency values
        import re
        currency_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        enhanced = re.sub(currency_pattern, r'**$\1**', enhanced)
        
        return enhanced
    
    def _extract_key_metrics(self, processed_result: dict, user_question: str) -> str:
        """Extract and format key numerical metrics from the data"""
        if not processed_result.get('success') or not processed_result.get('data'):
            return ""
        
        data = processed_result['data']
        columns = [c.lower() for c in processed_result.get('columns', [])]
        metrics = []
        
        try:
            # Find amount-related columns
            amount_columns = [i for i, col in enumerate(columns) if 'amount' in col or 'total' in col or 'price' in col]
            
            for col_idx in amount_columns:
                col_name = processed_result['columns'][col_idx]
                values = []
                
                for row in data:
                    if len(row) > col_idx and row[col_idx] is not None:
                        try:
                            # Handle both string and numeric values
                            val = float(str(row[col_idx]).replace(',', '').replace('$', ''))
                            values.append(val)
                        except:
                            continue
                
                if values:
                    total = sum(values)
                    avg = total / len(values)
                    max_val = max(values)
                    min_val = min(values)
                    
                    metrics.append(f"**{col_name.replace('_', ' ').title()}:**")
                    metrics.append(f"  • Total: ${total:,.2f}")
                    if len(values) > 1:
                        metrics.append(f"  • Average: ${avg:,.2f}")
                        metrics.append(f"  • Range: ${min_val:,.2f} - ${max_val:,.2f}")
        except:
            pass  # Skip if calculation fails
        
        return '\n'.join(metrics) if metrics else ""
    
    def _create_response_footer(self, processed_result: dict) -> str:
        """Create a helpful footer with context and tips"""
        if not processed_result.get('success'):
            return ""
        
        footer_parts = []
        
        # Add data source context
        if processed_result.get('items_expanded'):
            footer_parts.append("🔍 *This analysis includes detailed line-item data for comprehensive insights.*")
        
        # Add helpful reminders
        footer_parts.append("💡 *Tip: Try asking follow-up questions to explore specific aspects of your data.*")
        
        return '\n'.join(footer_parts) if footer_parts else ""

# Utility Functions for Streamlit UI
def display_results(results: dict):
    """Display results with intelligent item processing"""
    if not results.get("success") or not results.get("data"):
        st.error("No data to display")
        return
    
    # Check if results contain delimited item fields (using lowercase column names for PostgreSQL)
    has_item_columns = any(col in ['items_description', 'items_unit_price', 'items_quantity'] 
                          for col in results.get("columns", []))
    
    original_results = results
    display_expanded = False
    
    if has_item_columns:
        st.info("📦 This query contains invoice line items with detailed product/service information.")
        
        # Always auto-expand when item columns are present
        st.success("🔍 **Auto-expanded**: Showing individual line items for better visibility")
        results = delimited_processor.expand_results_with_items(results)
        display_expanded = True
        
        if results.get('items_expanded'):
            # Show item statistics
            item_response = delimited_processor.format_item_response(original_results, "")
            if item_response and item_response != "No detailed item information found in the query results.":
                st.markdown(item_response)
    
    # Use display data if available (excludes CASE_ID), otherwise filter it out
    if 'display_data' in results and 'display_columns' in results:
        df = pd.DataFrame(results["display_data"], columns=results["display_columns"])
    else:
        df = pd.DataFrame(results["data"], columns=results["columns"])
        # Hide CASE_ID column from frontend display
        if 'case_id' in df.columns:
            df = df.drop(columns=['case_id'])
        elif 'CASE_ID' in df.columns:
            df = df.drop(columns=['CASE_ID'])
    
    if df.empty:
        st.warning("Query returned no results")
        return
    
    # Data table with pagination
    st.subheader("📊 Query Results")
    
    # Show expansion info if applicable
    if results.get('items_expanded'):
        st.success(f"✅ Expanded from {results['original_row_count']} invoices to {results['expanded_row_count']} individual line items")
    
    # Add filters for large datasets
    if len(df) > 50:
        show_all_key = f"show_all_{hash(str(results.get('data', [])[:5]))}"  # Unique key based on data
        show_all = st.checkbox("Show all rows", value=False, key=show_all_key)
        if not show_all:
            df_display = df.head(50)
            st.caption(f"Showing first 50 rows of {len(df)} total rows")
        else:
            df_display = df
    else:
        df_display = df
    
    st.dataframe(df_display, use_container_width=True)

def create_query_suggestions():
    """Provide helpful query suggestions to users"""
    st.subheader("💡 Quick Questions")
    
    # Basic queries
    basic_suggestions = [
        "How many invoices do I have?",
        "What's my total unpaid balance?",
        "Show me overdue invoices",
        "What's the average invoice amount?"
    ]
    
    # Item-level queries including product-specific examples
    item_suggestions = [
        "What items did I purchase?",
        "Show me line item details", 
        "What's the price of cloud storage?",
        "How much did I spend on software licenses?",
        "What products are on my invoices?",
        "Break down my invoice items",
        "Show me all hosting services I bought",
        "What's the cost of support services?"
    ]
    
    # Create tabs for different types of queries
    tab1, tab2 = st.tabs(["💰 Financial Queries", "📦 Item Details"])
    
    with tab1:
        col1, col2 = st.columns(2)
        for i, suggestion in enumerate(basic_suggestions):
            with col1 if i % 2 == 0 else col2:
                if st.button(suggestion, key=f"basic_suggestion_{i}", use_container_width=True):
                    st.session_state.suggested_query = suggestion
                    st.rerun()
    
    with tab2:
        st.info("📦 These queries will show detailed breakdowns of individual items on your invoices")
        col1, col2 = st.columns(2)
        for i, suggestion in enumerate(item_suggestions):
            with col1 if i % 2 == 0 else col2:
                if st.button(suggestion, key=f"item_suggestion_{i}", use_container_width=True):
                    st.session_state.suggested_query = suggestion
                    st.rerun()
    return None

def create_help_section():
    """Create comprehensive help section"""
    with st.expander("❓ Help & Documentation"):
        st.markdown("""
        ### How to Use FinOpSysAI
        
        1. **Initialize System**: Click "🚀 Initialize System" in the sidebar
        2. **Set Vendor Context**: Load cases and select a Case ID
        3. **Ask Questions**: Use natural language to query your financial data
        
        ### Example Questions
        
        **Financial Queries:**
        - "How many invoices do I have?"
        - "What's my total unpaid balance?"
        - "Show me invoices over $1000"
        - "Which invoices are overdue?"
        
        **Item-Level Queries:**
        - "What items did I purchase?"
        - "Show me line item details"
        - "What products are on my invoices?"
        - "Break down invoice items by price"
        
        **Product-Specific Queries:**
        - "What's the price of cloud storage?"
        - "How much did I spend on software licenses?"
        - "Show me all hosting services I bought"
        - "What's the cost of support services?"
        - "Find invoices with 'backup' products"
        - "How much did consulting cost?"
        
        ### Available Columns
        - **CASE_ID**: Case identifier
        - **VENDOR_ID**: Vendor identifier  
        - **AMOUNT**: Total invoice amount
        - **BALANCE_AMOUNT**: Unpaid balance
        - **PAID**: Amount paid
        - **STATUS**: Invoice status
        - **BILL_DATE**: Bill date
        - **DUE_DATE**: Payment due date
          ### Item Detail Columns (Enhanced JSON Array Support)
        - **ITEMS_DESCRIPTION**: Product/service names (JSON arrays or CSV)
        - **ITEMS_UNIT_PRICE**: Price per item (JSON arrays or CSV)
        - **ITEMS_QUANTITY**: Quantity per item (JSON arrays or CSV)
        
        **Supported Formats:**
        - JSON Arrays: `["Cloud Storage", "Support"]` or `[99.99, 150.00]`
        - CSV Format: `"Cloud Storage,Support"` or `"99.99,150.00"`
        
        💡 **Automatic Processing**: The system automatically detects and expands item details 
        when you query item-level data, showing each product/service as a separate row.
        
        ### Security Features
        - All queries are automatically filtered by your vendor context
        - Only SELECT operations are allowed
        - Query validation prevents SQL injection
        - Rate limiting prevents abuse
        """)

def show_system_metrics():
    """Display system performance metrics"""
    with st.expander("🔍 System Metrics"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Session Duration", 
                     f"{(datetime.now() - st.session_state.get('login_time', datetime.now())).seconds // 60} min")
        
        with col2:
            st.metric("Total Queries", len(st.session_state.get('messages', [])))
        
        with col3:
            active_provider = st.session_state.chat_app.llm_manager.active_provider if 'chat_app' in st.session_state else "None"
            st.metric("AI Provider", active_provider.title() if active_provider else "Not Set")
            
        # Debug information for troubleshooting
        if st.checkbox("🔧 Show Debug Info"):
            debug_info = {
                "Last Processed Query": st.session_state.get('last_processed_query', 'None'),
                "Processing in Progress": st.session_state.get('processing_in_progress', False),
                "Current Request ID": st.session_state.get('current_request_id', 'None'),
                "Last Processing Time": str(st.session_state.get('last_processed_time', 'None')),
                "Vendor Context Set": st.session_state.get('vendor_context_set', False),
                "Available Providers": st.session_state.chat_app.llm_manager.available_providers if 'chat_app' in st.session_state else []
            }
            
            st.json(debug_info)

# Streamlit App
def main():
    # Security check - session timeout
    SecurityManager.check_session_timeout()
    
    # Generate session ID if not exists
    if 'session_id' not in st.session_state:
        st.session_state.session_id = SecurityManager.generate_session_id()
        st.session_state.login_time = datetime.now()
    
    st.set_page_config(
        page_title="FinOpSysAI",
        page_icon="💼",
        layout="wide"
    )
    
    st.title("💼 FinOpSysAI")
    st.caption("Finopsys financial data assistant - AI-powered invoice analysis")
    
    # Initialize session state
    if 'chat_app' not in st.session_state:
        st.session_state.chat_app = ContextAwareChat()
        st.session_state.initialized = False
        st.session_state.vendor_context_set = False
        st.session_state.vendor_context_logged = False
        st.session_state.messages = []
        # Store vendor context in session state for persistence
        st.session_state.vendor_id = None
        st.session_state.case_id = None
    
    # Always restore vendor context to database manager if it exists in session state
    # This ensures context persists across page reloads and streamlit reruns
    if (st.session_state.vendor_context_set and 
        st.session_state.vendor_id and 
        st.session_state.case_id):
        # Only restore if not already set to avoid duplicate logging
        if (st.session_state.chat_app.db_manager.vendor_id != st.session_state.vendor_id or
            st.session_state.chat_app.db_manager.case_id != st.session_state.case_id):
            st.session_state.chat_app.db_manager.vendor_id = st.session_state.vendor_id
            st.session_state.chat_app.db_manager.case_id = st.session_state.case_id
            
            # Only log if this is a new restoration (not already logged in this session)
            if not st.session_state.get('vendor_context_logged', False):
                logger.info(f"🔄 Restored vendor context: case_id={st.session_state.case_id}, vendor_id={st.session_state.vendor_id}")
                st.session_state.vendor_context_logged = True
        
    # Verify vendor context is properly set
    if st.session_state.vendor_context_set:
        if not st.session_state.chat_app.db_manager.vendor_id:
            logger.warning("⚠️ Vendor context flag set but db_manager.vendor_id is None - forcing restoration")
            st.session_state.chat_app.db_manager.vendor_id = st.session_state.vendor_id
            st.session_state.chat_app.db_manager.case_id = st.session_state.case_id
    
    # Sidebar for system status and controls
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Initialize system
        if not st.session_state.initialized:
            if st.button("🚀 Initialize System", type="primary"):
                with st.spinner("Initializing LLM and Database..."):
                    success = st.session_state.chat_app.initialize()
                    if success:
                        st.session_state.initialized = True
                        st.success("✅ System initialized successfully!")
                        st.rerun()
                    else:
                        st.error("❌ System initialization failed!")
        else:
            st.success("✅ System Online")
            
            # AI Model Selection
            st.header("🤖 AI Model Settings")
            
            # Show available providers
            available_providers = st.session_state.chat_app.llm_manager.available_providers
            if available_providers:
                current_provider = st.session_state.chat_app.llm_manager.active_provider
                
                # Provider selection
                selected_provider = st.selectbox(
                    "Select AI Provider:",
                    available_providers,
                    index=available_providers.index(current_provider) if current_provider in available_providers else 0,
                    format_func=lambda x: {
                        'openai': '🚀 OpenAI',
                        'gemini': '🔍 Google Gemini', 
                        'ollama': '🏠 Ollama (Local)'
                    }.get(x, x.title())
                )
                
                # Model selection for the selected provider
                available_models = st.session_state.chat_app.llm_manager.get_available_models(selected_provider)
                if available_models:
                    # Get current model or default
                    current_model = getattr(st.session_state, 'selected_model', available_models[0])
                    selected_model = st.selectbox(
                        "Select Model:",
                        available_models,
                        index=available_models.index(current_model) if current_model in available_models else 0
                    )
                    
                    # Update provider and model if changed
                    if selected_provider != current_provider:
                        st.session_state.chat_app.llm_manager.set_active_provider(selected_provider)
                        st.session_state.selected_model = selected_model
                        st.rerun()
                    elif getattr(st.session_state, 'selected_model', None) != selected_model:
                        st.session_state.selected_model = selected_model
                
                # Show current active configuration
                st.info(f"**Active:** {selected_provider.title()} - {getattr(st.session_state, 'selected_model', 'Default')}")
            else:
                st.error("❌ No AI providers available")
            
            # Show active LLM provider
            provider = st.session_state.chat_app.llm_manager.active_provider
            if provider == "openai":
                st.success("🚀 OpenAI Active")
            elif provider == "gemini":
                st.success("🔍 Google Gemini Active")
            elif provider == "ollama":
                st.success("🏠 Ollama Local Active")
            
            # Vendor context management
            st.header("👥 Vendor Context")
            
            if not st.session_state.vendor_context_set:
                # Get available cases
                if st.button("📋 Load Available Cases"):
                    with st.spinner("Loading cases..."):
                        cases = st.session_state.chat_app.db_manager.get_available_cases()
                        if cases:
                            st.session_state.available_cases = cases
                            st.success(f"✅ Found {len(cases)} cases")
                        else:
                            st.error("❌ No cases found")
                
                # Case selection
                if 'available_cases' in st.session_state:
                    selected_case = st.selectbox(
                        "Select Case ID:",
                        st.session_state.available_cases,
                        key="case_selector"
                    )
                    
                    if st.button("🔒 Set Vendor Context", type="primary"):
                        with st.spinner("Setting vendor context..."):
                            success = st.session_state.chat_app.db_manager.set_vendor_context(selected_case)
                            if success:
                                st.session_state.vendor_context_set = True
                                st.session_state.vendor_context_logged = False  # Reset logging flag for new context
                                # Store vendor context in session state for persistence
                                st.session_state.vendor_id = st.session_state.chat_app.db_manager.vendor_id
                                st.session_state.case_id = st.session_state.chat_app.db_manager.case_id
                                # Clear any cached query analysis since we have a new context
                                if hasattr(st.session_state.chat_app, '_cached_query_analysis'):
                                    delattr(st.session_state.chat_app, '_cached_query_analysis')
                                st.success("✅ Vendor context established!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to set vendor context")
            else:
                # Show current context with debugging
                vendor_id = st.session_state.chat_app.db_manager.vendor_id
                case_id = st.session_state.chat_app.db_manager.case_id
                
                st.success(f"🔒 **Active Context:**")
                st.write(f"• **Case ID:** {case_id}")
                st.write(f"• **Vendor ID:** {vendor_id}")
                
                # Debug session state values
                with st.expander("🔍 Debug Info"):
                    st.write(f"Session vendor_context_set: {st.session_state.vendor_context_set}")
                    st.write(f"Session vendor_id: {st.session_state.vendor_id}")
                    st.write(f"Session case_id: {st.session_state.case_id}")
                    st.write(f"DB Manager vendor_id: {st.session_state.chat_app.db_manager.vendor_id}")
                    st.write(f"DB Manager case_id: {st.session_state.chat_app.db_manager.case_id}")
                
                if st.button("🔄 Reset Context"):
                    st.session_state.chat_app.db_manager.vendor_id = None
                    st.session_state.chat_app.db_manager.case_id = None
                    st.session_state.vendor_context_set = False
                    st.session_state.vendor_context_logged = False
                    # Clear vendor context from session state
                    st.session_state.vendor_id = None
                    st.session_state.case_id = None
                    st.session_state.messages = []
                    st.rerun()            
            st.divider()
            
            # Compliance status
            st.header("⚖️ Compliance Status")
            if st.session_state.vendor_context_set:
                st.success("✅ Vendor filtering active")
                st.success("✅ Session context locked")
                st.success("✅ Query restrictions enforced")
            else:
                st.warning("⚠️ No vendor context set")
      # Main chat interface
    if st.session_state.initialized and st.session_state.vendor_context_set:
        st.header("💬 Chat Interface")
        st.info("💼 Ask questions about your financial data using natural language!")
        
        # Add query suggestions and help
        create_query_suggestions()
        create_help_section()
        show_system_metrics()
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Enhanced display for assistant messages
                if message["role"] == "assistant":
                    # Add a subtle container for better visual separation
                    with st.container():
                        st.markdown(message["content"])
                else:
                    st.markdown(message["content"])
                
                # If this is an assistant message with query results, display them
                if (message["role"] == "assistant" and 
                    "data" in message and 
                    isinstance(message["data"], dict)):
                    display_results(message["data"])
        
        # Chat input - Fixed implementation
        prompt = None
        
        # Check if a suggestion was clicked
        if st.session_state.get('suggested_query', None):
            prompt = st.session_state.suggested_query
            st.session_state.suggested_query = None  # Clear the suggestion
            
        # Get chat input
        chat_input = st.chat_input("Ask about your financial data...")
        if chat_input:
            prompt = chat_input
        
        # Process the prompt with enhanced duplicate prevention
        if prompt:
            # Create a unique request ID for this processing session
            import hashlib
            import time
            request_id = hashlib.md5(f"{prompt}{time.time()}{id(st.session_state)}".encode()).hexdigest()[:8]
            
            # Enhanced duplicate prevention with multiple checks
            current_time = datetime.now()
            last_processed_query = st.session_state.get('last_processed_query', None)
            last_processed_time = st.session_state.get('last_processed_time', datetime.min)
            processing_in_progress = st.session_state.get('processing_in_progress', False)
            last_request_id = st.session_state.get('last_request_id', None)
            
            # Check if same query is currently being processed
            if processing_in_progress and last_processed_query == prompt:
                logger.warning(f"⚠️ Query already being processed (request_id: {request_id}): {prompt}")
                st.warning("⏳ This query is already being processed. Please wait...")
                return
            
            # Check if same query was processed very recently (within 5 seconds)
            time_since_last = (current_time - last_processed_time).total_seconds()
            if (last_processed_query == prompt and time_since_last < 5):
                logger.warning(f"⚠️ Skipping duplicate query (request_id: {request_id}, time_since: {time_since_last:.1f}s): {prompt}")
                st.info(f"⏳ This query was processed {time_since_last:.1f} seconds ago. Please wait before resubmitting.")
                return
            
            # Check if this is a repeat submission of the exact same request
            if last_request_id and st.session_state.get('processing_completed', True) == False:
                logger.warning(f"⚠️ Previous request still processing (last_id: {last_request_id}, new_id: {request_id})")
                st.warning("⏳ Previous request is still being processed. Please wait...")
                return
            
            # Mark processing as in progress with enhanced tracking
            st.session_state.processing_in_progress = True
            st.session_state.processing_completed = False
            st.session_state.last_processed_query = prompt
            st.session_state.last_processed_time = current_time
            st.session_state.current_request_id = request_id
            st.session_state.last_request_id = request_id
            
            # Add to request log for debugging with enhanced info
            if 'request_log' not in st.session_state:
                st.session_state.request_log = []
            st.session_state.request_log.append({
                'time': current_time.strftime('%H:%M:%S.%f')[:-3],  # Include milliseconds
                'request_id': request_id,
                'query': prompt[:50] + "..." if len(prompt) > 50 else prompt,
                'status': 'started'
            })
            # Keep only last 15 entries for better debugging
            if len(st.session_state.request_log) > 15:
                st.session_state.request_log = st.session_state.request_log[-15:]
            
            logger.info(f"🔄 Starting query processing (request_id: {request_id}): {prompt}")
            
            # Clear previous cache if this is a different query
            if last_processed_query and last_processed_query != prompt:
                st.session_state.chat_last_processed_query = None
                st.session_state.chat_last_query_response = None
                logger.info(f"🧹 Cleared cache for new query (request_id: {request_id})")
            
            try:
                # Add user message to history with duplicate prevention
                last_message = st.session_state.messages[-1] if st.session_state.messages else None
                user_message_exists = (last_message and 
                                     last_message.get("content") == prompt and 
                                     last_message.get("role") == "user")
                
                if not user_message_exists:
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": prompt,
                        "request_id": request_id,
                        "timestamp": current_time.isoformat()
                    })
                    logger.info(f"📝 Added user message to history (request_id: {request_id})")
                else:
                    logger.info(f"📝 User message already exists in history (request_id: {request_id})")
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate and display response with enhanced error handling
                with st.chat_message("assistant"):
                    with st.spinner(f"🤖 Processing your query... (ID: {request_id})"):
                        try:
                            response = st.session_state.chat_app.process_user_query(prompt)
                            
                            # Enhanced response display with better formatting
                            st.markdown(response)
                            
                            # Update request log
                            for log_entry in st.session_state.request_log:
                                if log_entry['request_id'] == request_id:
                                    log_entry['status'] = 'completed'
                                    break
                            
                            # Check for and display query results with enhanced handling
                            results_displayed = False
                            if hasattr(st.session_state.chat_app.db_manager, 'last_query_result'):
                                results = st.session_state.chat_app.db_manager.last_query_result
                                if results and results.get("success"):
                                    display_results(results)
                                    results_displayed = True
                                    
                                    # Store message with data for persistence (enhanced duplicate prevention)
                                    last_assistant_message = st.session_state.messages[-1] if st.session_state.messages else None
                                    assistant_message_exists = (last_assistant_message and 
                                                              last_assistant_message.get("role") == "assistant" and 
                                                              last_assistant_message.get("content") == response and
                                                              last_assistant_message.get("request_id") != request_id)
                                    
                                    if not assistant_message_exists:
                                        st.session_state.messages.append({
                                            "role": "assistant", 
                                            "content": response,
                                            "data": results,
                                            "request_id": request_id,
                                            "timestamp": datetime.now().isoformat(),
                                            "has_results": True
                                        })
                                        logger.info(f"📝 Added assistant message with results (request_id: {request_id})")
                                    else:
                                        logger.info(f"📝 Assistant message with results already exists (request_id: {request_id})")
                            
                            # Store message without data if no results
                            if not results_displayed:
                                last_assistant_message = st.session_state.messages[-1] if st.session_state.messages else None
                                assistant_message_exists = (last_assistant_message and 
                                                          last_assistant_message.get("role") == "assistant" and 
                                                          last_assistant_message.get("content") == response and
                                                          last_assistant_message.get("request_id") != request_id)
                                
                                if not assistant_message_exists:
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": response,
                                        "request_id": request_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "has_results": False
                                    })
                                    logger.info(f"📝 Added assistant message without results (request_id: {request_id})")
                                else:
                                    logger.info(f"📝 Assistant message without results already exists (request_id: {request_id})")
                            
                            logger.info(f"✅ Completed processing (request_id: {request_id})")
                                
                        except Exception as e:
                            error_msg = f"❌ Error processing query: {str(e)}"
                            st.error(error_msg)
                            
                            # Update request log
                            for log_entry in st.session_state.request_log:
                                if log_entry['request_id'] == request_id:
                                    log_entry['status'] = 'error'
                                    log_entry['error'] = str(e)
                                    break
                            
                            # Store error message with duplicate prevention
                            last_assistant_message = st.session_state.messages[-1] if st.session_state.messages else None
                            error_message_exists = (last_assistant_message and 
                                                  last_assistant_message.get("role") == "assistant" and 
                                                  last_assistant_message.get("content") == error_msg and
                                                  last_assistant_message.get("request_id") != request_id)
                            
                            if not error_message_exists:
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": error_msg,
                                    "request_id": request_id,
                                    "timestamp": datetime.now().isoformat(),
                                    "error": True
                                })
                                logger.info(f"📝 Added error message (request_id: {request_id})")
                            
                            logger.error(f"❌ Query processing error (request_id: {request_id}): {str(e)}")
            
            finally:
                # Always clear processing flags with enhanced cleanup
                st.session_state.processing_in_progress = False
                st.session_state.processing_completed = True
                logger.info(f"🏁 Processing completed and flags cleared (request_id: {request_id})")
    
    elif st.session_state.initialized:
        st.info("👆 Please select a case ID in the sidebar to establish vendor context")
    else:
        st.info("👆 Please initialize the system using the sidebar")

if __name__ == "__main__":
    main()
