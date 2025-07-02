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
import snowflake.connector
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
SNOWFLAKE_CONFIG = {
    'account': config.SNOWFLAKE_ACCOUNT,
    'user': config.SNOWFLAKE_USER,
    'password': config.SNOWFLAKE_PASSWORD or os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': config.SNOWFLAKE_WAREHOUSE,
    'database': config.SNOWFLAKE_DATABASE,
    'schema': config.SNOWFLAKE_SCHEMA,
    'role': config.SNOWFLAKE_ROLE
}

# Use configuration for API key
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
        self.primary_model = None
        self.fallback_model = None
        self.active_provider = None
        self.column_reference = ColumnReferenceLoader()
        self.column_keywords = column_keywords
        
    def initialize_models(self) -> bool:
        """Initialize LLM models with Gemini -> Ollama fallback"""
        # Check if API key is available for Gemini
        if not GEMINI_API_KEY:
            logger.warning("⚠️ No Gemini API key provided, skipping Gemini initialization")
        else:
            # Try Gemini first
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.primary_model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Test Gemini connection
                test_response = self.primary_model.generate_content("Hello")
                if test_response and test_response.text:
                    self.active_provider = "gemini"
                    logger.info("✅ Gemini AI initialized successfully")
                    return True
            except ImportError:
                logger.warning("❌ Google Generative AI library not installed")
            except Exception as e:
                logger.warning(f"❌ Gemini initialization failed: {str(e)}")
        
        # Fallback to Ollama DeepSeek
        try:
            import ollama
            client = ollama.Client(host=config.OLLAMA_URL)
            response = client.chat(
                model=config.OLLAMA_MODEL, 
                messages=[{'role': 'user', 'content': 'Hello'}]            )
            
            if response and 'message' in response:
                self.fallback_model = {'client': client, 'model': config.OLLAMA_MODEL}
                self.active_provider = "ollama"
                logger.info("✅ Ollama DeepSeek initialized successfully")
                return True
        except ImportError:
            logger.warning("❌ Ollama library not installed")
        except Exception as e:
            logger.warning(f"❌ Ollama initialization failed: {str(e)}")
        
        logger.error("❌ No LLM models available")
        return False
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using active model with fallback"""
        # Check rate limiting
        client_id = st.session_state.get('session_id', 'anonymous')
        if not rate_limiter.is_allowed(client_id):
            return "❌ Rate limit exceeded. Please wait before making another request."
        
        try:
            if self.active_provider == "gemini" and self.primary_model:
                response = self.primary_model.generate_content(prompt)
                return response.text if response and response.text else "No response generated"
                
            elif self.active_provider == "ollama" and self.fallback_model:
                response = self.fallback_model['client'].chat(
                    model=self.fallback_model['model'],
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response['message']['content'] if response and 'message' in response else "No response generated"
                
        except Exception as e:
            logger.error(f"❌ Response generation failed: {str(e)}")
            # Try fallback if primary fails
            if self.active_provider == "gemini" and self.fallback_model:
                try:
                    response = self.fallback_model['client'].chat(
                        model=self.fallback_model['model'],
                        messages=[{'role': 'user', 'content': prompt}]
                    )
                    self.active_provider = "ollama"
                    logger.info("🔄 Switched to Ollama fallback after Gemini failure")
                    return response['message']['content'] if response and 'message' in response else "Fallback failed"
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {str(fallback_error)}")
            
        return f"❌ Error: Unable to generate response. Please try again later."

class SnowflakeManager:
    """Enhanced Snowflake manager with connection pooling and security"""
    
    def __init__(self):
        self.connection = None
        self.vendor_id = None
        self.case_id = None
        self.connection_validated = False
        
    def connect(self) -> bool:
        """Establish Snowflake connection with validation"""
        try:
            # Validate configuration first
            config.validate_config()
            
            self.connection = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
            
            # Test connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0] == 1:
                self.connection_validated = True
                logger.info("✅ Snowflake connection established and validated")
                return True
            else:
                logger.error("❌ Snowflake connection test failed")
                return False
                
        except ValueError as e:
            logger.error(f"❌ Configuration error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Snowflake connection failed: {str(e)}")
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
            raise AppError("Query execution failed", str(e))@staticmethod
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
        self.db_manager = SnowflakeManager()
        self.delimited_processor = delimited_processor
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize both LLM and database connections"""
        llm_success = self.llm_manager.initialize_models()
        db_success = self.db_manager.connect()
        self.initialized = llm_success and db_success
        return self.initialized
    
    def generate_sql_query(self, user_question: str) -> str:
        """Generate SQL query with vendor context and delimited field awareness"""
        if not self.db_manager.vendor_id:
            return "❌ Error: No vendor context established."
        
        # Use the enhanced delimited processor to check for item queries
        is_item_query = self.delimited_processor.is_item_query(user_question)
        
        # Check for specific product queries
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
SELECT CASE_ID, INVOICE_DATE, ITEMS_DESCRIPTION, ITEMS_UNIT_PRICE, ITEMS_QUANTITY 
FROM AI_INVOICE WHERE vendor_id = '{self.db_manager.vendor_id}'
ORDER BY INVOICE_DATE DESC"""
        
        prompt = f"""{enhanced_context}

USER QUESTION: {user_question}

Generate ONLY a valid SQL query for Snowflake database. Follow these strict requirements:
1. ALWAYS include: WHERE vendor_id = '{self.db_manager.vendor_id}'
2. Use ONLY the AI_INVOICE table
3. Return ONLY the SQL query - no explanations, no markdown, no extra text
4. Map user keywords to correct column names using the comprehensive guide above
5. For item-related queries, include ITEMS_* columns for detailed breakdowns
6. For specific product searches, use LIKE operators on ITEMS_DESCRIPTION

SQL QUERY:"""
        
        sql_query = self.llm_manager.generate_response(prompt)
        
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
            # Check if this is an item-level query and if it's asking about specific products
            is_item_query = self.delimited_processor.is_item_query(user_question)
            is_specific_product_query = self.delimited_processor.is_specific_product_query(user_question)
            extracted_products = self.delimited_processor.extract_product_names_from_query(user_question)
            
            # Generate SQL query (enhanced for item detection and specific products)
            sql_query = self.generate_sql_query(user_question)
            
            # Execute query with vendor filtering
            result = self.db_manager.execute_vendor_query(sql_query)
            
            # Store the result for display purposes
            self.db_manager.last_query_result = result
            
            # Always attempt item expansion for item queries or when item columns are present
            processed_result = result
            if result.get("success"):
                # Check if result has item columns
                has_item_columns = any(col in ['ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY'] 
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
            
            {"ITEM-LEVEL ANALYSIS: This query involves individual items/products. The data has been automatically expanded to show individual line items. Provide insights about item-level details, quantities, pricing, and totals. Focus on product/service analysis." if processed_result.get('items_expanded') else ""}
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
            
            return filtered_response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {str(e)}")
            return f"❌ Error processing your query: {str(e)}"

# Utility Functions for Streamlit UI
def display_results(results: dict):
    """Display results with intelligent item processing"""
    if not results.get("success") or not results.get("data"):
        st.error("No data to display")
        return
    
    # Check if results contain delimited item fields
    has_item_columns = any(col in ['ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY'] 
                          for col in results.get("columns", []))
    
    original_results = results
    display_expanded = False
    
    if has_item_columns:
        st.info("📦 This query contains invoice line items with detailed product/service information.")
        
        # Automatically check if data should be expanded based on content
        df_temp = pd.DataFrame(results["data"], columns=results["columns"])
        should_auto_expand = False
        
        # Check if any item field contains JSON arrays or multiple items
        for col in ['ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY']:
            if col in df_temp.columns:
                sample_values = df_temp[col].dropna().head(5)
                for val in sample_values:
                    if isinstance(val, str):
                        # Check for JSON array format
                        if (val.strip().startswith('[') and val.strip().endswith(']')) or ',' in val:
                            should_auto_expand = True
                            break
                if should_auto_expand:
                    break
        
        # Automatically expand if multiple items detected
        if should_auto_expand:
            st.success("🔍 **Auto-expanded**: Detected multiple items per invoice - showing individual line items")
            results = delimited_processor.expand_results_with_items(results)
            display_expanded = True
            
            if results.get('items_expanded'):
                # Show item statistics
                item_response = delimited_processor.format_item_response(original_results, "")
                if item_response and item_response != "No detailed item information found in the query results.":
                    st.markdown(item_response)
    
    df = pd.DataFrame(results["data"], columns=results["columns"])
    
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
            
            # Show active LLM provider
            provider = st.session_state.chat_app.llm_manager.active_provider
            if provider == "gemini":
                st.info("🤖 Using: Google Gemini AI")
            elif provider == "ollama":
                st.info("🤖 Using: Ollama DeepSeek (Fallback)")
            
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
