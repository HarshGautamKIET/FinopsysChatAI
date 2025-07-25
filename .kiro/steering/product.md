# FinOpSysAI Product Overview

FinOpSysAI is Finopsys' financial data assistant designed to help users analyze invoice data. This secure, production-ready application provides vendor-specific database querying with an AI-powered natural language interface.

## Core Features

- **AI-Powered Querying**: Natural language interface to query financial data using multiple LLM providers (OpenAI GPT, Google Gemini, Ollama DeepSeek)
- **Vendor Context Management**: Strict vendor-specific data filtering and context management for security
- **Item Processing**: Intelligent parsing and expansion of JSON arrays and CSV item data
- **Export Options**: Download results in CSV, Excel, and JSON formats
- **Security First**: Comprehensive security measures including SQL injection protection and rate limiting

## Data Model

The application works with invoice data stored in a PostgreSQL database with the following key entities:
- Invoices with vendor context, financial details, and status information
- Line items stored in structured formats (JSON arrays or CSV) within invoice records
- Vendor and case relationships for proper data isolation

## User Interaction Flow

1. User initializes the system and establishes vendor context
2. User asks natural language questions about their financial data
3. System translates questions to secure SQL queries with proper vendor filtering
4. Results are displayed with automatic item expansion when appropriate
5. User can export or further analyze the data

## Security Constraints

- All queries must include vendor filtering
- Only SELECT operations are allowed
- Sensitive identifiers (case_id, vendor_id, etc.) must not be exposed to users
- Rate limiting and session management are enforced