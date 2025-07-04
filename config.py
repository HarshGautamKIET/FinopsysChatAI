import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Centralized configuration management with validation"""
    # Database
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: Optional[str] = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DATABASE: str = os.getenv('POSTGRES_DATABASE', 'finopsys_db')
    POSTGRES_SCHEMA: str = os.getenv('POSTGRES_SCHEMA', 'public')
      # AI Models
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OLLAMA_URL: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
    DEFAULT_PROVIDER: str = os.getenv('DEFAULT_PROVIDER', 'gemini')
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'gemini-1.5-flash')    
    # Application
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '3600'))
    MAX_QUERY_RESULTS: int = int(os.getenv('MAX_QUERY_RESULTS', '1000'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Feedback System
    DEVELOPMENT_MODE: bool = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    FAISS_INDEX_PATH: str = os.getenv('FAISS_INDEX_PATH', './feedback_data/faiss_index')
    FEEDBACK_DATA_PATH: str = os.getenv('FEEDBACK_DATA_PATH', './feedback_data/feedback.json')
    FEEDBACK_SIMILARITY_THRESHOLD: float = float(os.getenv('FEEDBACK_SIMILARITY_THRESHOLD', '0.85'))
    FEEDBACK_MAX_RESULTS: int = int(os.getenv('FEEDBACK_MAX_RESULTS', '5'))
    
    # Security Settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '30'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    
    def get(self, key: str, default=None):
        """Get configuration value by key"""
        return getattr(self, key, default)
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.POSTGRES_HOST:
            raise ValueError("POSTGRES_HOST environment variable is required")
        if not self.POSTGRES_USER:
            raise ValueError("POSTGRES_USER environment variable is required")
        if not self.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD environment variable is required")
        if not self.POSTGRES_DATABASE:
            raise ValueError("POSTGRES_DATABASE environment variable is required")
        if self.DEFAULT_PROVIDER == 'gemini' and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required when using Gemini as default provider")
        
        # Validate feedback system settings
        if self.DEVELOPMENT_MODE and not self.FAISS_INDEX_PATH:
            raise ValueError("FAISS_INDEX_PATH is required when DEVELOPMENT_MODE is enabled")
        
        return True