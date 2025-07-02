import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Centralized configuration management with validation"""    # Database
    SNOWFLAKE_ACCOUNT: str = os.getenv('SNOWFLAKE_ACCOUNT', '')
    SNOWFLAKE_USER: str = os.getenv('SNOWFLAKE_USER', '')
    SNOWFLAKE_PASSWORD: Optional[str] = os.getenv('SNOWFLAKE_PASSWORD')
    SNOWFLAKE_WAREHOUSE: str = os.getenv('SNOWFLAKE_WAREHOUSE', 'FINOPSYS_WH')
    SNOWFLAKE_DATABASE: str = os.getenv('SNOWFLAKE_DATABASE', 'FINOPSYS_DB')
    SNOWFLAKE_SCHEMA: str = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
    SNOWFLAKE_ROLE: str = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
      # AI Models
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    OLLAMA_URL: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
    DEFAULT_PROVIDER: str = os.getenv('DEFAULT_PROVIDER', 'gemini')
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'gemini-1.5-flash')    
    # Application
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '3600'))
    MAX_QUERY_RESULTS: int = int(os.getenv('MAX_QUERY_RESULTS', '1000'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.SNOWFLAKE_ACCOUNT:
            raise ValueError("SNOWFLAKE_ACCOUNT environment variable is required")
        if not self.SNOWFLAKE_USER:
            raise ValueError("SNOWFLAKE_USER environment variable is required")
        if not self.SNOWFLAKE_PASSWORD:
            raise ValueError("SNOWFLAKE_PASSWORD environment variable is required")
        if self.DEFAULT_PROVIDER == 'gemini' and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required when using Gemini as default provider")
        return True