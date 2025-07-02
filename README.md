# 💼 FinOpSysAI

**FinOpSysAI** is Finopsys' financial data assistant designed to help you analyze your invoice data. This secure, production-ready application provides vendor-specific database querying with AI-powered natural language interface.

## ✨ Features

- **🔒 Security First**: Comprehensive security measures including SQL injection protection, rate limiting, and session management
- **🤖 AI-Powered**: Multi-provider AI support (Google Gemini, OpenAI GPT, Ollama) with user-selectable models
- **👥 Vendor Context**: Strict vendor-specific data filtering and context management
- **🛠️ Vector Feedback System**: Developer feedback with semantic search and prompt enhancement
- **📊 Item Processing**: Intelligent parsing and expansion of JSON arrays and CSV item data
- **📥 Export Options**: Download results in CSV, Excel, and JSON formats
- **⚡ Performance Optimized**: Query caching, optimization hints, and connection management
- **🎨 User-Friendly**: Intuitive interface with query suggestions and comprehensive help

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
- Snowflake account with access credentials
- Optional: Google Gemini API key for enhanced AI features

### Installation

1. **Navigate to the application directory**
```bash
cd chatbot_SQL
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your actual credentials
# Required:
SNOWFLAKE_ACCOUNT=your_account_here
SNOWFLAKE_USER=your_username_here
SNOWFLAKE_PASSWORD=your_password_here
SNOWFLAKE_WAREHOUSE=your_warehouse_here
SNOWFLAKE_DATABASE=your_database_here

# Optional (for enhanced AI features):
GEMINI_API_KEY=your_api_key_here
```

4. **Run the application**
```bash
streamlit run streamlit/src/app.py
```

5. **Access the application**
- Open your browser to `http://localhost:8501`
- Initialize the system using the sidebar
- Select a case ID to establish vendor context
- Start asking questions about your data!
## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SNOWFLAKE_ACCOUNT` | ✅ | - | Your Snowflake account identifier |
| `SNOWFLAKE_USER` | ✅ | - | Snowflake username |
| `SNOWFLAKE_PASSWORD` | ✅ | - | Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | ✅ | `COMPUTE_WH` | Snowflake warehouse name |
| `SNOWFLAKE_DATABASE` | ✅ | `DEMO_DB` | Snowflake database name |
| `SNOWFLAKE_SCHEMA` | ❌ | `PUBLIC` | Snowflake schema name |
| `SNOWFLAKE_ROLE` | ❌ | `ACCOUNTADMIN` | Snowflake role |
| `GEMINI_API_KEY` | ❌ | - | Google Gemini API key |
| `OPENAI_API_KEY` | ❌ | - | OpenAI API key |
| `OPENAI_MODEL` | ❌ | `gpt-3.5-turbo` | OpenAI model name |
| `OLLAMA_URL` | ❌ | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | ❌ | `deepseek-r1:1.5b` | Ollama model name |
| `SESSION_TIMEOUT` | ❌ | `3600` | Session timeout in seconds |
| `MAX_QUERY_RESULTS` | ❌ | `1000` | Maximum query result rows |
| `RATE_LIMIT_REQUESTS` | ❌ | `30` | Rate limit requests per minute |
| `DEVELOPMENT_MODE` | ❌ | `false` | Enable feedback UI (true/false) |
| `FAISS_INDEX_PATH` | ❌ | `./feedback_data/faiss_index` | FAISS vector index file path |
| `FEEDBACK_DATA_PATH` | ❌ | `./feedback_data/feedback.json` | Feedback JSON data file path |
| `FEEDBACK_SIMILARITY_THRESHOLD` | ❌ | `0.85` | Feedback similarity threshold (0.0-1.0) |
| `FEEDBACK_MAX_RESULTS` | ❌ | `5` | Max similar feedback items to retrieve |

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

## 🛠️ Vector Feedback System

FinOpSysAI includes a comprehensive feedback system for improving AI response quality through developer insights.

### Features
- **🔍 Semantic Search**: Vector-based similarity search using FAISS and Gemini embeddings
- **📝 Developer Portal**: Complete feedback management interface (development mode only)
- **🚀 Prompt Enhancement**: Automatic injection of relevant feedback during inference
- **📊 Analytics**: Comprehensive feedback statistics and export tools
- **🔐 Security**: Development/production mode toggle for secure deployment

### Quick Setup
```bash
# Run the automated setup
python setup_feedback_system.py

# Or manual setup
pip install faiss-cpu>=1.7.4

# Configure environment
echo "DEVELOPMENT_MODE=true" >> .env
echo "FAISS_INDEX_PATH=./feedback_data/faiss_index" >> .env
```

### Usage
1. Enable development mode: `DEVELOPMENT_MODE=true` in `.env`
2. Use the application normally to generate AI responses
3. Access "🛠️ Developer Feedback Portal" in the sidebar
4. Provide feedback, corrections, and improvements
5. Test retrieval system and view analytics

For detailed documentation, see [`FEEDBACK_SYSTEM_README.md`](FEEDBACK_SYSTEM_README.md)

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

## 🛠️ Development

### Project Structure

```
FinOpSysAI/
├── streamlit/src/app.py              # Main application
├── utils/
│   ├── error_handler.py              # Error handling utilities
│   ├── query_validator.py            # SQL query validation
│   ├── query_optimizer.py            # Query optimization
│   └── delimited_field_processor.py  # Item processing utilities
├── config.py                         # Configuration management
├── column_reference_loader.py        # Database column mapping
├── column_keywords_mapping.py        # Keywords mapping
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
└── README.md                         # This file
```

### Testing

```bash
# Run the application in development mode
streamlit run streamlit/src/app.py --server.port 8501

# For production deployment, consider using:
# - Gunicorn or similar WSGI server
# - Docker containers
# - Load balancers
# - Database connection pooling
```

## 🚨 Security Fixes Applied

This version includes comprehensive security improvements:

- ✅ Removed all hardcoded credentials
- ✅ Implemented comprehensive SQL injection protection
- ✅ Added rate limiting and session management
- ✅ Enhanced error handling and logging
- ✅ Added query validation and optimization
- ✅ Implemented secure session management

See `SECURITY_FIXES_SUMMARY.md` for detailed information.

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
   - Wait for the rate limit window to reset
   - Reduce query frequency
   - Contact administrator for limit adjustments

### Getting Help

- Check the help section in the application (❓ icon)
- Review error messages in the application logs
- Ensure all environment variables are properly set
- Verify database schema matches expectations

## 📄 License

This project is proprietary software. See `LICENSE` file for details.

## 🔮 Future Enhancements

- **Multi-tenant Support**: Support for multiple organizations
- **Advanced Analytics**: Custom dashboards and reporting
- **API Endpoints**: REST API for programmatic access
- **Real-time Notifications**: Alerts and updates
- **Enhanced Security**: Multi-factor authentication, OAuth
- **Performance**: Redis caching, connection pooling
- **Mobile Support**: Responsive design improvements

---

**💼 Ready to get started?** Follow the Quick Start guide above and begin exploring your financial data with FinOpSysAI's AI-powered natural language queries!
