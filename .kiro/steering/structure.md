# FinOpSysAI Project Structure

## Directory Organization

```
FinOpSysAI/
├── streamlit/                      # Streamlit application
│   └── src/                        # Application source code
│       └── app.py                  # Main application entry point
├── utils/                          # Utility modules
│   ├── delimited_field_processor.py # Item processing utilities
│   ├── error_handler.py            # Error handling utilities
│   ├── query_optimizer.py          # Query optimization
│   └── query_validator.py          # SQL query validation
├── .yoyo/                          # Database migration files
├── config.py                       # Configuration management
├── column_reference_loader.py      # Database column mapping
├── column_keywords_mapping.py      # Keywords mapping
├── llm_response_restrictions.py    # LLM response security
├── run_streamlit.py                # Streamlit runner script
├── start_app.py                    # Application starter
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── README.md                       # Project documentation
```

## Key Files and Their Purposes

### Core Application

- **streamlit/src/app.py**: Main Streamlit application with UI components and user interaction flow
- **run_streamlit.py**: Convenience script to start the Streamlit application
- **start_app.py**: Alternative application starter

### Configuration and Setup

- **config.py**: Centralized configuration management with environment variable loading
- **.env.example**: Template for environment variables
- **requirements.txt**: Python package dependencies

### Data Processing

- **column_reference_loader.py**: Loads and manages database column reference information
- **column_keywords_mapping.py**: Maps natural language keywords to database columns
- **utils/delimited_field_processor.py**: Processes JSON and CSV item data in invoices

### Security and Validation

- **llm_response_restrictions.py**: Enforces security restrictions on LLM responses
- **utils/query_validator.py**: Validates SQL queries for security compliance
- **utils/error_handler.py**: Error handling utilities

### Testing and Debugging

- **test_*.py**: Various test files for different components
- **debug_openai_app.py**: Debug utilities for OpenAI integration
- **diagnose_gemini.py**: Diagnostic tools for Gemini integration
- **validate_system.py**: System validation utilities

## Code Organization Patterns

1. **Centralized Configuration**: All configuration is managed through the `Config` class in `config.py`
2. **Utility Modules**: Common functionality is organized into utility modules in the `utils/` directory
3. **Security-First Design**: Security validation is integrated at multiple levels
4. **Component Separation**: Clear separation between data processing, query generation, and UI components
5. **Test Coverage**: Comprehensive test files for different components

## Development Conventions

1. **Environment Variables**: All configuration should be loaded from environment variables
2. **Security Validation**: All database queries must include vendor filtering
3. **Error Handling**: Use structured error handling with appropriate logging
4. **Documentation**: Include docstrings and comments for all functions and classes
5. **Type Hints**: Use Python type hints for better code clarity