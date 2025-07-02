import logging
import traceback
from functools import wraps
from typing import Any, Callable

class AppError(Exception):
    """Custom application error with user-friendly messages"""
    def __init__(self, message: str, technical_details: str = None):
        self.message = message
        self.technical_details = technical_details
        super().__init__(message)

def error_handler(user_message: str = "An error occurred"):
    """Decorator for consistent error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except AppError as e:
                logging.error(f"Application error in {func.__name__}: {e.technical_details}")
                return {"success": False, "error": e.message}
            except Exception as e:
                logging.error(f"Unexpected error in {func.__name__}: {traceback.format_exc()}")
                return {"success": False, "error": user_message}
        return wrapper
    return decorator