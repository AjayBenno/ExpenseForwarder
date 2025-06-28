"""Configuration module for expense forwarder."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the expense forwarder."""
    
    # OpenAI API settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Splitwise API settings
    SPLITWISE_CLIENT_ID: Optional[str] = os.getenv("SPLITWISE_CLIENT_ID")
    SPLITWISE_CLIENT_SECRET: Optional[str] = os.getenv("SPLITWISE_CLIENT_SECRET")
    SPLITWISE_REDIRECT_URI: str = os.getenv("SPLITWISE_REDIRECT_URI", "http://localhost:8080/callback")
    SPLITWISE_BASE_URL: str = "https://secure.splitwise.com/api/v3.0"
    SPLITWISE_AUTH_URL: str = "https://secure.splitwise.com/oauth/authorize"
    SPLITWISE_TOKEN_URL: str = "https://secure.splitwise.com/oauth/token"
    
    # Default expense settings
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    
    @staticmethod
    def _get_default_group_id() -> Optional[int]:
        """Get default group ID from environment variable."""
        group_id_str = os.getenv("DEFAULT_GROUP_ID")
        if group_id_str and group_id_str != "your_default_group_id_here":
            try:
                return int(group_id_str)
            except ValueError:
                pass
        return None
    
    DEFAULT_GROUP_ID: Optional[int] = _get_default_group_id()
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        required_vars = [
            cls.OPENAI_API_KEY,
            cls.SPLITWISE_CLIENT_ID,
            cls.SPLITWISE_CLIENT_SECRET
        ]
        
        missing_vars = [var for var in required_vars if not var]
        if missing_vars:
            print(f"Missing required environment variables: {len(missing_vars)} variables")
            return False
        
        return True

# Global config instance
config = Config() 