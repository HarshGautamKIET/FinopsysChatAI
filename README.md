# 💼 FinOpSysAI

**FinOpSysAI** is Finopsys' AI-powered financial data assistant designed to help you analyze invoice data through natural language queries. ## 📦 Advanced Item Processing Features

The application intelligently handles invoice line items stored as JSON arrays or structured strings within single database fields, enabling sophisticated item-level analysis.

### Virtual Row Expansion Technology

**Data Structure (Current):**
Product line items are stored as aligned JSON arrays in these columns:
- `ITEMS_DESCRIPTION` → e.g., `["Cable", "Connector", "Software"]`
- `ITEMS_UNIT_PRICE` → e.g., `[150, 75, 250]`
- `ITEMS_QUANTITY` → e.g., `[10, 5, 1]`

**Virtual Transformation:**
The system automatically transforms each array element into individual rows:
```
| ITEM_NAME  | UNIT_PRICE | QUANTITY | LINE_TOTAL |
|------------|------------|----------|------------|
| Cable      | 150        | 10       | 1500.00    |
| Connector  | 75         | 5        | 375.00     |
| Software   | 250        | 1        | 250.00     |
```

### LLM-Powered Query Understanding

**Intelligent Detection:**
- Automatically detects item-level queries like "What is the most expensive item?"
- Recognizes product-specific searches like "Show me cloud storage costs"
- Identifies quantity-related questions like "List items with quantity > 5"

**Query Examples That Trigger Virtual Expansion:**
- "What items did I purchase?"
- "Show me the most expensive item in invoice X"
- "List all items with quantity > 5"
- "What's the price of cloud storage?"
- "Show me item names in my last invoice"
- "Break down my invoice by individual products"

### Supported Data Formats
- **JSON Arrays**: `["Cloud Storage", "Support"]` or `[99.99, 150.00]`
- **CSV Format**: `"Cloud Storage,Support"` or `"99.99,150.00"`
- **Mixed Formats**: The system handles both formats within the same dataset

### Automatic Processing Features
- **Smart Detection**: Identifies item columns (`ITEMS_DESCRIPTION`, `ITEMS_UNIT_PRICE`, `ITEMS_QUANTITY`)
- **Format Agnostic**: Parses both JSON arrays and CSV-delimited strings seamlessly
- **Virtual Expansion**: Converts multi-item invoices into individual line item rows
- **Statistical Analysis**: Provides item-level statistics, totals, and insights
- **Product Search**: Enables searching for specific products across all invoices

### Enhanced User Experience
- **Automatic Expansion**: No manual intervention required - the system detects when to expand
- **Clear Messaging**: Users are informed when virtual expansion occurs
- **Rich Analytics**: Item statistics, common products, and pricing insights
- **Performance Optimized**: Efficient processing even with large datasetstion-ready application provides vendor-specific database access with intelligent AI-powered analysis.

## ✨ Core Features

- **🔒 Enterprise Security**: Multi-layer SQL injection protection, rate limiting, session management, and audit logging
- **🤖 Multi-Provider AI**: Google Gemini, OpenAI GPT, and Ollama DeepSeek with automatic fallback
- **👥 Vendor Context Management**: Strict vendor-specific data filtering with session-persistent context
- **🧠 Intelligent Feedback System**: Vector-based feedback enhancement with semantic search capabilities
- **📊 Advanced Item Processing**: Smart parsing of JSON arrays and CSV item data with automatic expansion
- **� Flexible Export**: Download results in CSV, Excel, and JSON formats
- **⚡ High Performance**: Query caching, optimization, connection pooling, and result limiting
- **🎨 Intuitive Interface**: User-friendly design with query suggestions and comprehensive help system

## 🛡️ Security Features

- **SQL Injection Protection**: Multi-layer query validation and sanitization
- **Rate Limiting**: 30 requests per minute per session (configurable)
- **Session Management**: Secure sessions with 1-hour timeout
- **Environment-based Configuration**: No hardcoded credentials
- **Audit Logging**: Comprehensive security event logging
- **Query Restrictions**: Only SELECT operations allowed with vendor filtering

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Snowflake account with proper credentials
- API keys for AI providers (Google Gemini recommended)

### Installation

1. **Clone or extract the application**
```powershell
# Navigate to the application directory
cd "e:\Finopsys\FinOpsysChatAI\chatbot_SQL - Copy"
```

2. **Install required dependencies**
```powershell
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file in the root directory with your credentials:
```env
# Required Database Configuration
SNOWFLAKE_ACCOUNT=your_account_here
SNOWFLAKE_USER=your_username_here
SNOWFLAKE_PASSWORD=your_password_here
SNOWFLAKE_WAREHOUSE=your_warehouse_here
SNOWFLAKE_DATABASE=your_database_here
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN

# Optional AI Provider Keys (at least one recommended)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Advanced Configuration
DEVELOPMENT_MODE=false
SESSION_TIMEOUT=3600
MAX_QUERY_RESULTS=1000
RATE_LIMIT_REQUESTS=30
```

4. **Launch the application**
```powershell
streamlit run streamlit/src/app.py
```

5. **Access the application**
- Open your browser to `http://localhost:8501`
- Initialize the system using the sidebar options
- Select a case ID to establish vendor context
- Start querying your financial data!
## 🔧 Configuration

### Core Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SNOWFLAKE_ACCOUNT` | ✅ | - | Your Snowflake account identifier |
| `SNOWFLAKE_USER` | ✅ | - | Snowflake username |
| `SNOWFLAKE_PASSWORD` | ✅ | - | Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | ✅ | `COMPUTE_WH` | Snowflake warehouse name |
| `SNOWFLAKE_DATABASE` | ✅ | `DEMO_DB` | Snowflake database name |
| `SNOWFLAKE_SCHEMA` | ❌ | `PUBLIC` | Snowflake schema name |
| `SNOWFLAKE_ROLE` | ❌ | `ACCOUNTADMIN` | Snowflake role |

### AI Provider Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ❌ | - | Google Gemini API key (recommended) |
| `OPENAI_API_KEY` | ❌ | - | OpenAI API key |
| `OPENAI_MODEL` | ❌ | `gpt-3.5-turbo` | OpenAI model name |
| `OLLAMA_URL` | ❌ | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | ❌ | `deepseek-r1:1.5b` | Ollama model name |

### Advanced Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEVELOPMENT_MODE` | ❌ | `false` | Enable feedback UI (true/false) |
| `SESSION_TIMEOUT` | ❌ | `3600` | Session timeout in seconds |
| `MAX_QUERY_RESULTS` | ❌ | `1000` | Maximum query result rows |
| `RATE_LIMIT_REQUESTS` | ❌ | `30` | Rate limit requests per minute |
| `FAISS_INDEX_PATH` | ❌ | `./feedback_data/faiss_index` | FAISS vector index path |
| `FEEDBACK_DATA_PATH` | ❌ | `./feedback_data/feedback.json` | Feedback data path |
| `FEEDBACK_SIMILARITY_THRESHOLD` | ❌ | `0.85` | Feedback similarity threshold |
| `FEEDBACK_MAX_RESULTS` | ❌ | `5` | Max feedback items to retrieve |

### Database Schema

The application expects a table named `AI_INVOICE` with the following structure:

```sql
CREATE TABLE AI_INVOICE (
    CASE_ID VARCHAR,
    VENDOR_ID VARCHAR,
    AMOUNT NUMBER,
    BALANCE_AMOUNT NUMBER,
    PAID NUMBER,
    STATUS VARCHAR,
    BILL_DATE DATE,
    DUE_DATE DATE,
    -- Additional columns as needed
);
```

## 🎮 Usage Guide

### 1. System Initialization
- Click "🚀 Initialize System" in the sidebar
- Wait for both AI models and database connection to be established

### 2. Vendor Context Setup
- Click "📋 Load Available Cases" to see available case IDs
- Select a case ID from the dropdown
- Click "🔒 Set Vendor Context" to establish secure vendor filtering

### 3. Querying Data
Use natural language to ask questions about your data:

**Example Questions:**
- "How many invoices do I have?"
- "What's my total unpaid balance?"
- "Show me invoices over $1000"
- "Which invoices are overdue?"
- "What's the average invoice amount?"

### 4. Viewing Results
- Results are displayed in interactive tables
- Automatic expansion for item-level data
- Pagination for large datasets

## � Item Processing Features

The application intelligently handles invoice line items stored in multiple formats:

### Supported Formats
- **JSON Arrays**: `["Cloud Storage", "Support"]` or `[99.99, 150.00]`
- **CSV Format**: `"Cloud Storage,Support"` or `"99.99,150.00"`

### Automatic Processing
- **Detection**: Automatically identifies item columns (ITEMS_DESCRIPTION, ITEMS_UNIT_PRICE, ITEMS_QUANTITY)
- **Parsing**: Supports both JSON and CSV formats within the same dataset
- **Expansion**: Converts multi-item invoices into individual line item rows
- **Analysis**: Provides item-level statistics and insights

### Example Queries
- "What items did I purchase?"
- "Show me line item details"
- "What products are on my invoices?"
- "Break down my invoice items"

## 🛠️ Intelligent Feedback System

FinOpSysAI includes an advanced vector-based feedback system that continuously improves AI response quality through developer insights and semantic enhancement.

### Key Capabilities
- **🔍 Vector-Based Search**: FAISS-powered semantic similarity using Gemini embeddings
- **📝 Developer Portal**: Comprehensive feedback management interface (development mode)
- **🚀 Automatic Enhancement**: Real-time injection of relevant feedback during AI inference
- **📊 Performance Analytics**: Detailed feedback statistics and data export tools
- **🔐 Environment-Aware**: Secure development/production mode toggle

### Quick Setup for Development
```powershell
# Install vector search dependencies
pip install faiss-cpu>=1.7.4

# Enable development mode in .env
echo "DEVELOPMENT_MODE=true" | Out-File -Append .env

# Initialize feedback system (optional - auto-created on first use)
mkdir feedback_data -ErrorAction SilentlyContinue
```

### Usage Workflow
1. **Enable Development Mode**: Set `DEVELOPMENT_MODE=true` in your `.env` file
2. **Generate Responses**: Use the application normally to create AI responses
3. **Provide Feedback**: Access "🛠️ Developer Feedback Portal" in the sidebar
4. **Review Analytics**: Monitor feedback effectiveness and system improvements
5. **Export Data**: Download feedback data for analysis and backup

## 🔒 Security Best Practices

### For Administrators

1. **Environment Security**
   - Keep `.env` files secure and private
   - Use strong, unique passwords for database accounts
   - Regularly rotate API keys and credentials
   - Set appropriate session timeouts

2. **Network Security**
   - Deploy behind HTTPS/TLS
   - Use reverse proxy (nginx/Apache) for production
   - Implement network-level access controls
   - Consider VPN access for sensitive environments

3. **Monitoring**
   - Monitor rate limit violations
   - Track security events in logs
   - Set up alerting for suspicious activities
   - Regular security audits

### For Users

1. **Session Management**
   - Log out when finished
   - Don't share session URLs
   - Use secure networks only
   - Report any suspicious behavior

2. **Query Guidelines**
   - Only SELECT operations are allowed
   - All queries are automatically filtered by your vendor context
   - Large result sets are automatically limited
   - Use specific questions for better performance

## 🛠️ Development & Architecture

### Project Structure

```
FinOpSysAI/
├── streamlit/src/app.py              # Main Streamlit application
├── feedback/                         # Feedback system components
│   ├── manager.py                    # Feedback management
│   ├── ui_components.py              # UI components
│   └── vector_store.py               # Vector storage
├── utils/                           # Core utilities
│   ├── error_handler.py              # Error handling
│   ├── query_validator.py            # SQL validation
│   ├── query_optimizer.py            # Query optimization
│   └── delimited_field_processor.py  # Item processing
├── config.py                         # Configuration management
├── column_reference_loader.py        # Database schema mapping
├── column_keywords_mapping.py        # Keyword mappings
├── llm_response_restrictions.py      # LLM response control
├── requirements.txt                  # Python dependencies
├── .env                              # Environment configuration
└── README.md                         # Documentation
```

### System Validation

```powershell
# Validate system integrity after setup
python validate_system.py

# Run the application
streamlit run streamlit/src/app.py --server.port 8501
```

### Production Deployment Considerations

- **HTTPS/TLS**: Deploy behind secure proxy (nginx/Apache)
- **Load Balancing**: Distribute traffic across multiple instances
- **Database Pooling**: Implement connection pooling for scalability
- **Monitoring**: Set up application and infrastructure monitoring
- **Backup**: Regular backup of feedback data and configurations
- **Security**: Network access controls and VPN for sensitive data

## 🚨 Production-Ready Security

This version is production-ready with comprehensive security implementations:

- ✅ **Zero Hardcoded Credentials**: All credentials managed via environment variables
- ✅ **Advanced SQL Injection Protection**: Multi-layer query validation and sanitization
- ✅ **Rate Limiting & Session Management**: Configurable limits with secure session handling
- ✅ **Comprehensive Error Handling**: Robust error management with detailed logging
- ✅ **Query Validation & Optimization**: Performance-optimized with security validation
- ✅ **Vendor Context Isolation**: Strict data access controls per vendor
- ✅ **Audit Logging**: Complete security event tracking and monitoring

## 📈 Performance Optimizations

- **Query Caching**: 5-minute TTL for frequently used queries
- **Connection Management**: Proper database connection handling
- **Result Limiting**: Automatic limits on large datasets
- **Query Optimization**: Performance hints and index usage
- **UI Optimization**: Efficient data rendering and pagination

## 🤝 Support

### Common Issues

1. **Database Connection Failed**
   - Verify Snowflake credentials in `.env`
   - Check network connectivity
   - Ensure warehouse and database names are correct

2. **No AI Model Available**
   - Check Gemini API key if using Google Gemini
   - Ensure Ollama is running if using local models
   - Verify API endpoints are accessible

3. **Rate Limit Exceeded**
   - Wait for the rate limit window to reset (1 minute)
   - Reduce query frequency
   - Contact administrator for limit adjustments

4. **Session Timeout**
   - Sessions expire after 1 hour for security
   - Re-initialize the system if prompted
   - Check session timeout settings in configuration

### Getting Help

- Use the **❓ Help** section in the application sidebar
- Review error messages and logs for specific issues
- Ensure all required environment variables are properly configured
- Verify Snowflake database schema matches expected structure
- Check that your vendor context is properly established

### Support Resources

- **Application Logs**: Check console output for detailed error information
- **Network Connectivity**: Ensure proper access to Snowflake and API endpoints
- **Permissions**: Verify database and warehouse access permissions
- **System Requirements**: Confirm Python 3.8+ and all dependencies are installed

## 📄 License

This project is proprietary software owned by FinOpsysAI. See the `LICENSE` file for complete terms and conditions.

## 🔮 Roadmap & Future Enhancements

- **🏢 Multi-Tenant Architecture**: Support for multiple organizations and databases
- **📊 Advanced Analytics**: Custom dashboards, reporting, and data visualization
- **🔌 REST API**: Programmatic access endpoints for integration
- **🔔 Real-Time Notifications**: Alerts, webhooks, and automated reporting
- **🔐 Enhanced Authentication**: Multi-factor authentication, OAuth, SSO integration
- **⚡ Performance Scaling**: Redis caching, connection pooling, distributed processing
- **📱 Mobile Optimization**: Enhanced responsive design and mobile-first features
- **🤖 AI Model Management**: Fine-tuning, custom models, and advanced AI features

---

**� Ready to start analyzing your financial data?** 

Follow the Quick Start guide above to get FinOpSysAI running in your environment. Within minutes, you'll be asking natural language questions about your invoice data and getting AI-powered insights!
