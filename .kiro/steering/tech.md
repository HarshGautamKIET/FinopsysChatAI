# FinOpSysAI Technical Stack

## Core Technologies

- **Python 3.8+**: Primary programming language
- **PostgreSQL**: Database backend for storing invoice data
- **Streamlit**: Web framework for the user interface
- **Multiple LLM Providers**:
  - OpenAI GPT (primary)
  - Google Gemini
  - Ollama with DeepSeek model (local option)

## Key Dependencies

- **AI/ML Libraries**:
  - `openai`: OpenAI API client
  - `google-generativeai`: Google Gemini API client
  - `ollama`: Local LLM integration

- **Database**:
  - `psycopg2-binary`: PostgreSQL connector
  - `sqlalchemy`: SQL toolkit and ORM

- **Data Processing**:
  - `pandas`: Data manipulation and analysis
  - `numpy`: Numerical computing

- **Configuration & Security**:
  - `python-dotenv`: Environment variable management
  - `pydantic`: Data validation
  - `cryptography`: Cryptographic operations
  - `bcrypt`: Password hashing

## Environment Configuration

The application uses environment variables loaded from a `.env` file for configuration:
- Database credentials
- API keys for LLM providers
- Application settings (timeouts, rate limits, etc.)

## Common Commands

### Setup and Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Running the Application

```bash
# Start the Streamlit app directly
streamlit run streamlit/src/app.py

# Or use the convenience script
python run_streamlit.py
```

### Testing

```bash
# Test LLM connections
python test_llm_connections.py

# Test database connection
python test_db_connection.py

# Run specific test files
python test_expansion.py
python test_column_mapping.py
```

### Development

```bash
# Validate system configuration
python validate_system.py

# Debug OpenAI integration
python debug_openai_app.py

# Test Gemini integration
python diagnose_gemini.py
```