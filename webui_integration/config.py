"""
Configuration management for Open WebUI InfoBlox Integration
"""

import os
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WebUIConfig:
    """Configuration for Open WebUI integration."""
    
    # InfoBlox MCP Server settings
    mcp_server_path: str = "python3 infoblox-mcp-server.py"
    mcp_server_timeout: int = 30
    
    # LLM API settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    
    # Default models for each provider
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-haiku-20240307"
    groq_model: str = "llama-3.1-8b-instant"
    together_model: str = "meta-llama/Llama-3-8b-chat-hf"
    
    # Intent recognition settings
    intent_confidence_threshold: float = 0.6
    llm_confidence_threshold: float = 0.5
    
    # Response formatting settings
    max_table_rows: int = 20
    max_cell_length: int = 50
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None


class ConfigManager:
    """Manager for configuration settings."""
    
    def __init__(self, config_file: str = "webui_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> WebUIConfig:
        """Load configuration from file or environment."""
        config_data = {}
        
        # Load from file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {str(e)}")
        
        # Override with environment variables
        env_mappings = {
            "INFOBLOX_MCP_SERVER_PATH": "mcp_server_path",
            "INFOBLOX_MCP_TIMEOUT": "mcp_server_timeout",
            "OPENAI_API_KEY": "openai_api_key",
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GROQ_API_KEY": "groq_api_key",
            "TOGETHER_API_KEY": "together_api_key",
            "OPENAI_MODEL": "openai_model",
            "ANTHROPIC_MODEL": "anthropic_model",
            "GROQ_MODEL": "groq_model",
            "TOGETHER_MODEL": "together_model",
            "INTENT_CONFIDENCE_THRESHOLD": "intent_confidence_threshold",
            "LLM_CONFIDENCE_THRESHOLD": "llm_confidence_threshold",
            "LOG_LEVEL": "log_level",
            "LOG_FILE": "log_file"
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Convert types as needed
                if config_key in ["mcp_server_timeout", "max_table_rows", "max_cell_length"]:
                    config_data[config_key] = int(env_value)
                elif config_key in ["intent_confidence_threshold", "llm_confidence_threshold"]:
                    config_data[config_key] = float(env_value)
                else:
                    config_data[config_key] = env_value
        
        return WebUIConfig(**config_data)
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            config_dict = asdict(self.config)
            # Remove None values and sensitive data
            config_dict = {k: v for k, v in config_dict.items() 
                          if v is not None and not k.endswith('_api_key')}
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
    def get_available_llm_providers(self) -> List[str]:
        """Get list of available LLM providers based on API keys."""
        providers = []
        
        if self.config.openai_api_key:
            providers.append("openai")
        if self.config.anthropic_api_key:
            providers.append("anthropic")
        if self.config.groq_api_key:
            providers.append("groq")
        if self.config.together_api_key:
            providers.append("together")
        
        return providers
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check MCP server path
        if not self.config.mcp_server_path:
            issues.append("MCP server path not configured")
        
        # Check if at least one LLM provider is available
        if not self.get_available_llm_providers():
            issues.append("No LLM API keys configured - LLM fallback will be disabled")
        
        # Check confidence thresholds
        if not 0.0 <= self.config.intent_confidence_threshold <= 1.0:
            issues.append("Intent confidence threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.config.llm_confidence_threshold <= 1.0:
            issues.append("LLM confidence threshold must be between 0.0 and 1.0")
        
        return issues
    
    def setup_logging(self):
        """Setup logging based on configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config.log_file if self.config.log_file else None
        )
        
        logger.info(f"Logging configured: level={self.config.log_level}")


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> WebUIConfig:
    """Get the current configuration."""
    return config_manager.config


def setup_environment():
    """Setup environment for Open WebUI integration."""
    # Setup logging
    config_manager.setup_logging()
    
    # Validate configuration
    issues = config_manager.validate_config()
    if issues:
        logger.warning("Configuration issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    # Log available providers
    providers = config_manager.get_available_llm_providers()
    if providers:
        logger.info(f"Available LLM providers: {', '.join(providers)}")
    else:
        logger.warning("No LLM providers available - only intent recognition will work")
    
    logger.info("Environment setup complete")


# Example configuration file content
EXAMPLE_CONFIG = {
    "mcp_server_path": "python3 /path/to/infoblox-mcp-server.py",
    "mcp_server_timeout": 30,
    "openai_model": "gpt-4o-mini",
    "anthropic_model": "claude-3-haiku-20240307",
    "groq_model": "llama-3.1-8b-instant",
    "together_model": "meta-llama/Llama-3-8b-chat-hf",
    "intent_confidence_threshold": 0.6,
    "llm_confidence_threshold": 0.5,
    "max_table_rows": 20,
    "max_cell_length": 50,
    "log_level": "INFO"
}


def create_example_config():
    """Create an example configuration file."""
    config_file = Path("webui_config.example.json")
    
    try:
        with open(config_file, 'w') as f:
            json.dump(EXAMPLE_CONFIG, f, indent=2)
        
        print(f"Example configuration created: {config_file}")
        print("\nTo use this configuration:")
        print("1. Copy webui_config.example.json to webui_config.json")
        print("2. Edit the file with your settings")
        print("3. Set your API keys as environment variables:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("   export GROQ_API_KEY='your-key-here'")
        print("   export TOGETHER_API_KEY='your-key-here'")
        
    except Exception as e:
        print(f"Failed to create example config: {str(e)}")


if __name__ == "__main__":
    create_example_config()
