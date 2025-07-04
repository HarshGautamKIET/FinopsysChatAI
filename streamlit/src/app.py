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
from utils.enhanced_db_manager import EnhancedDatabaseManager
from column_reference_loader import ColumnReferenceLoader
from llm_response_restrictions import response_restrictions
from column_keywords_mapping import column_keywords

# Import feedback system
from feedback.manager import feedback_manager
from feedback.ui_components import show_feedback_ui, inject_feedback_into_session

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
GEMINI_API_KEY = config.GEMINI_API_KEY or os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = config.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
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
    """Manages LLM model initialization with user-selectable providers"""
    def __init__(self):
        self.gemini_model = None
        self.openai_client = None
        self.ollama_model = None
        self.active_provider = None
        self.available_providers = []
        self.provider_models = {}  # Store model references
        self.column_reference = ColumnReferenceLoader()
        self.column_keywords = column_keywords
        
    def initialize_models(self) -> bool:
        """Initialize all available LLM models"""
        success = False
        
        # Initialize Gemini
        if GEMINI_API_KEY:
            if not validate_api_key_format(GEMINI_API_KEY, 'gemini'):
                logger.warning("⚠️ Invalid Gemini API key format")
            else:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.gemini_model = genai.GenerativeModel(config.DEFAULT_MODEL)
                    # Test Gemini connection
                    test_response = self.gemini_model.generate_content("Hello")
                    if test_response and test_response.text:
                        self.available_providers.append('gemini')
                        self.provider_models['gemini'] = self.gemini_model
                        logger.info(f"✅ Google Gemini initialized successfully (API Key: {mask_api_key(GEMINI_API_KEY)})")
                        success = True
                except ImportError:
                    logger.warning("❌ Google Generative AI library not installed")
                except Exception as e:
                    logger.warning(f"⚠️ Gemini initialization failed: {str(e)}")
        else:
            logger.warning("⚠️ No Gemini API key provided")
        
        # Initialize OpenAI
        if OPENAI_API_KEY:
            if not validate_api_key_format(OPENAI_API_KEY, 'openai'):
                logger.warning("⚠️ Invalid OpenAI API key format")
            else:
                try:
                    import openai
                    
                    # Use the modern OpenAI client (v1.0+)
                    self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
                    
                    # Test the connection
                    test_response = self.openai_client.chat.completions.create(
                        model=config.OPENAI_MODEL,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    if test_response and test_response.choices:
                        self.available_providers.append('openai')
                        self.provider_models['openai'] = self.openai_client
                        logger.info(f"✅ OpenAI initialized successfully (API Key: {mask_api_key(OPENAI_API_KEY)})")
                        success = True
                        
                except ImportError:
                    logger.warning("❌ OpenAI library not installed")
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI initialization failed: {str(e)}")
        else:
            logger.warning("⚠️ No OpenAI API key provided")
        
        # Initialize Ollama
        try:
            import ollama
            client = ollama.Client(host=config.OLLAMA_URL)
            response = client.chat(
                model=config.OLLAMA_MODEL, 
                messages=[{'role': 'user', 'content': 'Hello'}]
            )
            
            if response and 'message' in response:
                self.ollama_model = {'client': client, 'model': config.OLLAMA_MODEL}
                self.available_providers.append('ollama')
                self.provider_models['ollama'] = self.ollama_model
                logger.info("✅ Ollama initialized successfully")
                success = True
        except ImportError:
            logger.warning("❌ Ollama library not installed")
        except Exception as e:
            logger.warning(f"⚠️ Ollama initialization failed: {str(e)}")
        
        # Set default active provider (Gemini first, then OpenAI, then Ollama)
        if self.available_providers:
            if 'gemini' in self.available_providers:
                self.active_provider = 'gemini'
            elif 'openai' in self.available_providers:
                self.active_provider = 'openai'
            elif 'ollama' in self.available_providers:
                self.active_provider = 'ollama'
            
            logger.info(f"🎯 Active provider set to: {self.active_provider}")
        else:
            logger.error("❌ No LLM models available")
        
        return success
    
    def set_active_provider(self, provider: str) -> bool:
        """Set the active LLM provider"""
        if provider in self.available_providers:
            self.active_provider = provider
            logger.info(f"🔄 Switched to provider: {provider}")
            return True
        else:
            logger.warning(f"⚠️ Provider {provider} not available")
            return False
    
    def get_provider_display_name(self, provider: str) -> str:
        """Get user-friendly display name for provider"""
        display_names = {
            'gemini': '🤖 Google Gemini',
            'openai': '🤖 OpenAI GPT',
            'ollama': '🤖 Ollama (Local)'
        }
        return display_names.get(provider, provider.title())
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using active model with fallback and feedback integration"""
        # Check rate limiting
        client_id = st.session_state.get('session_id', 'anonymous')
        if not rate_limiter.is_allowed(client_id):
            return "❌ Rate limit exceeded. Please wait before making another request."
        
        # Get feedback enhancement if development mode is enabled
        original_prompt = prompt
        if feedback_manager.development_mode:
            feedback_enhancement = feedback_manager.generate_feedback_prompt_enhancement(prompt)
            if feedback_enhancement:
                prompt = f"{feedback_enhancement}\n\n{prompt}"
                logger.info("🔄 Enhanced prompt with feedback guidance")
        
        try:
            if self.active_provider == "gemini" and self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                return response.text if response and response.text else "No response generated"
                
            elif self.active_provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content if response.choices else "No response generated"
                
            elif self.active_provider == "ollama" and self.ollama_model:
                response = self.ollama_model['client'].chat(
                    model=self.ollama_model['model'],
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response['message']['content'] if response and 'message' in response else "No response generated"
                
        except Exception as e:
            logger.error(f"❌ Response generation failed with {self.active_provider}: {str(e)}")
            
            # Try fallback providers
            fallback_providers = [p for p in self.available_providers if p != self.active_provider]
            for fallback_provider in fallback_providers:
                try:
                    logger.info(f"🔄 Trying fallback provider: {fallback_provider}")
                    
                    if fallback_provider == "gemini" and self.gemini_model:
                        response = self.gemini_model.generate_content(prompt)
                        if response and response.text:
                            return response.text
                            
                    elif fallback_provider == "openai" and self.openai_client:
                        response = self.openai_client.chat.completions.create(
                            model=config.OPENAI_MODEL,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=1000,
                            temperature=0.7
                        )
                        if response.choices:
                            return response.choices[0].message.content
                            
                    elif fallback_provider == "ollama" and self.ollama_model:
                        response = self.ollama_model['client'].chat(
                            model=self.ollama_model['model'],
                            messages=[{'role': 'user', 'content': prompt}]
                        )
                        if response and 'message' in response:
                            return response['message']['content']
                            
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback {fallback_provider} also failed: {str(fallback_error)}")
                    continue
            
        return f"❌ Error: Unable to generate response. All providers failed."

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
            raise AppError("Query execution failed", str(e))
    
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
        self.enhanced_db_manager = EnhancedDatabaseManager(self.db_manager)
        self.delimited_processor = delimited_processor
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize both LLM and database connections"""
        llm_success = self.llm_manager.initialize_models()
        db_success = self.db_manager.connect()
        self.initialized = llm_success and db_success
        return self.initialized
    
    def generate_sql_query(self, user_question: str) -> str:
        """Generate SQL query with enhanced item-aware LLM guidance"""
        if not self.db_manager.vendor_id:
            return "❌ Error: No vendor context established."
        
        # 🔹 NEW: Get enhanced LLM guidance for item-level queries
        enhanced_guidance = self.delimited_processor.create_enhanced_llm_prompt_guidance(
            user_question, self.db_manager.vendor_id
        )
        
        # Get base context from column keywords
        base_context = self.llm_manager.column_keywords.get_enhanced_prompt_context(
            self.db_manager.vendor_id, 
            self.db_manager.case_id
        )
        
        # Combine contexts for comprehensive LLM understanding
        combined_prompt = f"{base_context}\n\n{enhanced_guidance}"
        
        # Generate the SQL query using enhanced LLM guidance
        sql_query = self.llm_manager.generate_response(combined_prompt)
        
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
        
        logger.info(f"🔍 Generated enhanced SQL: {sql_query}")
        return sql_query
    
    def process_user_query(self, user_question: str) -> str:
        """Process user query with vendor context and automatic intelligent item handling"""
        if not self.initialized:
            return "❌ System not initialized. Please contact administrator."
        
        if not self.db_manager.vendor_id:
            return "❌ No vendor context established. Please select a case ID first."
        
        try:
            # Get comprehensive query analysis once (avoid redundant calls)
            query_analysis = self.delimited_processor.enhance_llm_understanding_for_items(user_question)
            is_item_query = query_analysis['is_item_query']
            is_specific_product_query = query_analysis['is_product_query']
            extracted_products = query_analysis['extracted_products']
            
            logger.info(f"🎯 Query analysis completed: Intent={query_analysis['query_intent']}, Item Query={is_item_query}, Product Query={is_specific_product_query}")
            
            # Generate SQL query (enhanced for item detection and specific products)
            sql_query = self.generate_sql_query(user_question)
            
            # 🔹 NEW: Use enhanced database manager for intelligent query execution with cached analysis
            processed_result = self.enhanced_db_manager.execute_item_aware_query_with_analysis(sql_query, user_question, query_analysis)
            
            # Store the processed result for display purposes
            self.db_manager.last_query_result = processed_result
            
            # Log expansion information
            if processed_result.get('items_expanded'):
                original_count = processed_result.get('original_row_count', 0)
                expanded_count = processed_result.get('expanded_row_count', 0)
                items_count = processed_result.get('total_line_items', expanded_count)
                logger.info(f"✅ Query results automatically expanded: {original_count} invoices → {items_count} line items")
            
            # Create safe context for LLM response
            safe_context = response_restrictions.create_safe_context_prompt(self.db_manager.vendor_id)
            
            # Generate natural language response with safety guidelines
            response_prompt = f"""
            {safe_context}
            
            {response_restrictions.get_response_guidelines()}
            
            Based on the following SQL query and result:
            
            Query: {sql_query}
            Result: {processed_result}
            User Question: {user_question}
            
            Provide a clear, concise answer to the user's question: {user_question}
            
            Remember: Never include specific ID values, case numbers, or vendor codes in your response.
            Focus on the data insights while maintaining privacy and security.
            
            {"ITEM-LEVEL ANALYSIS: This query involves individual items/products. The data has been automatically expanded to show individual line items with " + str(processed_result.get('total_line_items', 0)) + " total items. Provide insights about item-level details, quantities, pricing, and totals. Focus on product/service analysis." if processed_result.get('items_expanded') else ""}
            """
            final_response = self.llm_manager.generate_response(response_prompt)
            
            # Enhanced response formatting for specific product queries and general item queries
            if processed_result.get('items_expanded'):
                if is_specific_product_query and extracted_products:
                    # Use specialized product-specific response formatting
                    product_summary = self.delimited_processor.format_product_specific_response(
                        processed_result, user_question, extracted_products
                    )
                    if product_summary and "No information found" not in product_summary:
                        final_response = f"{final_response}\n\n{product_summary}"
                else:
                    # Use general item response formatting
                    item_summary = self.delimited_processor.format_item_response(processed_result, user_question)
                    if item_summary and "No detailed item information found" not in item_summary:
                        final_response = f"{final_response}\n\n{item_summary}"
            
            # Filter the response to remove any sensitive information
            filtered_response = response_restrictions.filter_response(final_response)
            
            # Store query and response in session state for feedback collection
            if feedback_manager.development_mode:
                st.session_state['last_user_query'] = user_question
                st.session_state['last_ai_response'] = filtered_response
                st.session_state['last_sql_query'] = sql_query
                st.session_state['vendor_id'] = self.db_manager.vendor_id
                st.session_state['case_id'] = getattr(self.db_manager, 'case_id', '')
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {str(e)}")
            return f"❌ Error processing your query: {str(e)}"

# Utility Functions for Streamlit UI
def display_results(results: dict):
    """Display results with intelligent item processing and enhanced information"""
    if not results.get("success") or not results.get("data"):
        st.warning("No data returned for this query.")
        return
    
    # Check if results were expanded for item-level analysis
    if results.get('items_expanded'):
        original_count = results.get('original_row_count', 0)
        expanded_count = results.get('expanded_row_count', 0)
        total_items = results.get('total_line_items', expanded_count)
        
        st.info(f"""
        **✨ Virtual Row Expansion Activated**
        
        Your query involved individual products/services. To provide detailed insights, the JSON arrays have been automatically parsed and expanded:
        
        - **{original_count}** invoices analyzed
        - **{total_items}** individual line items created
        - Each row below represents one product/service line item
        
        💡 This virtual expansion allows for item-specific analysis like "most expensive item" or "items with quantity > 5"
        """)
        
        # Show item statistics if available
        item_stats = delimited_processor.get_item_statistics(results)
        if item_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Line Items", f"{item_stats.get('total_line_items', 0):,}")
            
            with col2:
                st.metric("Unique Invoices", f"{item_stats.get('unique_invoices', 0):,}")
            
            with col3:
                total_value = item_stats.get('total_item_value', 0)
                st.metric("Total Item Value", f"${total_value:,.2f}" if total_value > 0 else "N/A")
            
            with col4:
                avg_price = item_stats.get('average_item_price', 0)
                st.metric("Avg Item Price", f"${avg_price:.2f}" if avg_price > 0 else "N/A")
        
        # Show most common items if available
        if item_stats and item_stats.get('most_common_items'):
            with st.expander("📦 Most Common Items", expanded=False):
                for item_info in item_stats['most_common_items'][:5]:
                    st.write(f"• **{item_info['item']}** - appears {item_info['count']} time(s)")
    
    else:
        # Check if this is a missed opportunity for expansion
        has_item_columns = any(col in ['ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY'] 
                              for col in results.get("columns", []))
        
        if has_item_columns:
            st.info("� Displaying invoice-level data with JSON item arrays. For individual item analysis, ask questions like 'What items did I buy?' or 'Show me the most expensive item'.")
        else:
            st.info("📊 Displaying standard invoice-level data.")
    
    df = pd.DataFrame(results["data"], columns=results["columns"])
    
    if df.empty:
        st.warning("Query returned no results")
        return
    
    # Add enhanced data display section
    st.subheader("📊 Query Results")
    
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
    
    # Enhanced dataframe display with better formatting
    st.dataframe(
        df_display, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "ITEM_LINE_TOTAL": st.column_config.NumberColumn(
                "Line Total",
                format="$%.2f"
            ),
            "ITEM_UNIT_PRICE": st.column_config.NumberColumn(
                "Unit Price", 
                format="$%.2f"
            ),
            "AMOUNT": st.column_config.NumberColumn(
                "Amount",
                format="$%.2f"
            ),
            "BALANCE_AMOUNT": st.column_config.NumberColumn(
                "Balance",
                format="$%.2f"
            ),
            "PAID": st.column_config.NumberColumn(
                "Paid",
                format="$%.2f"
            )
        }
    )
    
    # Download option removed as requested

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
        "What's the most expensive item?",
        "List all items with quantity > 5",
        "What's the price of cloud storage?",
        "How much did I spend on software licenses?",
        "What products are on my invoices?",
        "Break down my invoice items",
        "Show me all hosting services I bought",
        "What's the cost of support services?",
        "What items were billed in my last invoice?",
        "Show me itemized breakdown",
        "What's the cheapest item I bought?",
        "List all products with their prices",
        "How many different items did I order?",
        "What services did I purchase last month?"
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

# Security utilities for API key protection
def mask_api_key(api_key: str, show_chars: int = 4) -> str:
    """Mask API key for secure logging and display"""
    if not api_key:
        return "Not Set"
    if len(api_key) <= show_chars * 2:
        return "***"
    return f"{api_key[:show_chars]}***{api_key[-show_chars:]}"

def validate_api_key_format(api_key: str, provider: str) -> bool:
    """Validate API key format for different providers"""
    if not api_key:
        return False
    
    patterns = {
        'openai': api_key.startswith('sk-'),
        'gemini': api_key.startswith('AIza'),
        'ollama': True  # Ollama doesn't use API keys
    }
    
    return patterns.get(provider, False)

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
        st.session_state.messages = []
        # Store vendor context in session state for persistence
        st.session_state.vendor_id = None
        st.session_state.case_id = None
    
    # Initialize feedback system
    feedback_manager.set_development_mode(config.DEVELOPMENT_MODE)
    
    # Always restore vendor context to database manager if it exists in session state
    # This ensures context persists across page reloads and streamlit reruns
    if (st.session_state.vendor_context_set and 
        st.session_state.vendor_id and 
        st.session_state.case_id):
        # Always restore the vendor context to the database manager
        st.session_state.chat_app.db_manager.vendor_id = st.session_state.vendor_id
        st.session_state.chat_app.db_manager.case_id = st.session_state.case_id
        logger.info(f"🔄 Restored vendor context: case_id={st.session_state.case_id}, vendor_id={st.session_state.vendor_id}")
        
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
            
            # LLM Provider Selection
            st.header("🤖 AI Model Selection")
            if st.session_state.chat_app.llm_manager.available_providers:
                current_provider = st.session_state.chat_app.llm_manager.active_provider
                
                # Create provider options with display names
                provider_options = {}
                for provider in st.session_state.chat_app.llm_manager.available_providers:
                    display_name = st.session_state.chat_app.llm_manager.get_provider_display_name(provider)
                    provider_options[display_name] = provider
                
                # Find current selection index
                current_display_name = st.session_state.chat_app.llm_manager.get_provider_display_name(current_provider)
                try:
                    current_index = list(provider_options.keys()).index(current_display_name)
                except ValueError:
                    current_index = 0
                
                # Provider selection
                selected_display = st.selectbox(
                    "Choose AI Provider:",
                    options=list(provider_options.keys()),
                    index=current_index,
                    key="llm_provider_selector",
                    help="Select which AI model to use for generating responses"
                )
                
                selected_provider = provider_options[selected_display]
                
                # Update provider if changed
                if selected_provider != current_provider:
                    if st.session_state.chat_app.llm_manager.set_active_provider(selected_provider):
                        st.success(f"✅ Switched to {selected_display}")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to switch to {selected_display}")
                
                # Show current model details
                if current_provider == "gemini":
                    st.info(f"📝 Model: {config.DEFAULT_MODEL}")
                elif current_provider == "openai":
                    st.info(f"📝 Model: {config.OPENAI_MODEL}")
                elif current_provider == "ollama":
                    st.info(f"📝 Model: {config.OLLAMA_MODEL}")
            else:
                st.warning("⚠️ No AI providers available")
            
            # Show active LLM provider (legacy display for compatibility)
            provider = st.session_state.chat_app.llm_manager.active_provider
            if provider == "gemini":
                st.caption("🤖 Using: Google Gemini AI")
            elif provider == "openai":
                st.caption("🤖 Using: OpenAI GPT")
            elif provider == "ollama":
                st.caption("🤖 Using: Ollama (Local)")
            
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
                                # Store vendor context in session state for persistence
                                st.session_state.vendor_id = st.session_state.chat_app.db_manager.vendor_id
                                st.session_state.case_id = st.session_state.chat_app.db_manager.case_id
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
        
        # Show feedback UI if development mode is enabled
        show_feedback_ui()
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])                  # If this is an assistant message with query results, display them
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
        
        # Process the prompt
        if prompt:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display response
            with st.chat_message("assistant"):
                with st.spinner("Processing your query..."):
                    try:
                        response = st.session_state.chat_app.process_user_query(prompt)
                        st.markdown(response)
                        
                        # Check for and display query results
                        if hasattr(st.session_state.chat_app.db_manager, 'last_query_result'):
                            results = st.session_state.chat_app.db_manager.last_query_result
                            if results and results.get("success"):
                                display_results(results)
                                # Store message with data for persistence
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": response,
                                    "data": results
                                })
                            else:
                                # Store message without data
                                st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            # Store message without data
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                    except Exception as e:
                        error_msg = f"❌ Error processing query: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        logger.error(f"Query processing error: {str(e)}")
    
    elif st.session_state.initialized:
        st.info("👆 Please select a case ID in the sidebar to establish vendor context")
    else:
        st.info("👆 Please initialize the system using the sidebar")

if __name__ == "__main__":
    main()
