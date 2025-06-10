"""Enhanced error handling and logging for InfoBlox MCP Server."""

import logging
import traceback
from typing import Dict, Any, Optional
from functools import wraps


class InfoBloxMCPError(Exception):
    """Base exception for InfoBlox MCP Server."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(InfoBloxMCPError):
    """Configuration related errors."""
    pass


class AuthenticationError(InfoBloxMCPError):
    """Authentication related errors."""
    pass


class NetworkError(InfoBloxMCPError):
    """Network connectivity errors."""
    pass


class ValidationError(InfoBloxMCPError):
    """Input validation errors."""
    pass


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    
    # Create logger
    logger = logging.getLogger("infoblox_mcp")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create log file {log_file}: {str(e)}")
    
    return logger


def handle_exceptions(logger: Optional[logging.Logger] = None):
    """Decorator for handling exceptions in async functions."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except InfoBloxMCPError:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                # Log unexpected exceptions
                if logger:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                # Convert to our custom exception
                raise InfoBloxMCPError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    details={"function": func.__name__, "original_error": str(e)}
                )
        
        return wrapper
    return decorator


def validate_ip_address(ip_str: str) -> bool:
    """Validate IP address format."""
    import ipaddress
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def validate_network_cidr(network_str: str) -> bool:
    """Validate network CIDR format."""
    import ipaddress
    try:
        ipaddress.ip_network(network_str, strict=False)
        return True
    except ValueError:
        return False


def validate_hostname(hostname: str) -> bool:
    """Validate hostname format."""
    import re
    
    if not hostname or len(hostname) > 253:
        return False
    
    # Remove trailing dot if present
    if hostname.endswith('.'):
        hostname = hostname[:-1]
    
    # Check each label
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
            return False
    
    return True


def validate_mac_address(mac_str: str) -> bool:
    """Validate MAC address format."""
    import re
    
    # Common MAC address formats
    patterns = [
        r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  # XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$',    # XXXX.XXXX.XXXX
        r'^([0-9A-Fa-f]{12})$'                          # XXXXXXXXXXXX
    ]
    
    return any(re.match(pattern, mac_str) for pattern in patterns)


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitize user input."""
    if not isinstance(value, str):
        value = str(value)
    
    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


class ErrorHandler:
    """Centralized error handling for the MCP server."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def handle_api_error(self, error: Exception, context: str = "") -> str:
        """Handle InfoBlox API errors."""
        from .client import InfoBloxAPIError
        
        if isinstance(error, InfoBloxAPIError):
            self.logger.error(f"InfoBlox API error{' in ' + context if context else ''}: {str(error)}")
            
            # Map common errors to user-friendly messages
            if error.status_code == 401:
                return "Authentication failed. Please check your credentials."
            elif error.status_code == 403:
                return "Access denied. You don't have permission for this operation."
            elif error.status_code == 404:
                return "The requested resource was not found."
            elif error.status_code == 409:
                return "The operation conflicts with existing data."
            elif error.status_code == 500:
                return "InfoBlox server error. Please try again later."
            else:
                return f"InfoBlox API error: {str(error)}"
        
        else:
            self.logger.error(f"Unexpected error{' in ' + context if context else ''}: {str(error)}")
            return f"An unexpected error occurred: {str(error)}"
    
    def handle_validation_error(self, field: str, value: str, expected: str) -> str:
        """Handle validation errors."""
        message = f"Invalid {field}: '{value}'. Expected {expected}."
        self.logger.warning(f"Validation error: {message}")
        return message
    
    def handle_configuration_error(self, error: Exception) -> str:
        """Handle configuration errors."""
        message = f"Configuration error: {str(error)}"
        self.logger.error(message)
        return message
    
    def handle_network_error(self, error: Exception) -> str:
        """Handle network connectivity errors."""
        message = f"Network error: {str(error)}"
        self.logger.error(message)
        return "Unable to connect to InfoBlox. Please check network connectivity and server address."


def create_error_response(error_message: str, error_code: str = "GENERAL_ERROR") -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "success": False,
        "error": {
            "message": error_message,
            "code": error_code
        }
    }

