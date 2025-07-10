import os
from dataclasses import dataclass, field
from typing import Optional, List
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
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    OLLAMA_URL: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
    DEFAULT_PROVIDER: str = os.getenv('DEFAULT_PROVIDER', 'openai')
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
    
    # Available models configuration
    OPENAI_MODELS: List[str] = field(default_factory=lambda: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'])
    GEMINI_MODELS: List[str] = field(default_factory=lambda: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro'])    
    # Application
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '3600'))
    MAX_QUERY_RESULTS: int = int(os.getenv('MAX_QUERY_RESULTS', '1000'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
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
        if self.DEFAULT_PROVIDER == 'openai' and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required when using OpenAI as default provider")
        if self.DEFAULT_PROVIDER == 'gemini' and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required when using Gemini as default provider")
        return True