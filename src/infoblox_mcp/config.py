"""Configuration management for InfoBlox MCP Server."""

import json
import os
import getpass
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from .error_handling import ConfigurationError, validate_ip_address


class InfoBloxConfig(BaseModel):
    """InfoBlox configuration model."""
    
    grid_master_ip: str = Field(..., description="InfoBlox Grid Master IP address")
    username: str = Field(..., description="InfoBlox username")
    password: str = Field(..., description="Encrypted InfoBlox password")
    wapi_version: str = Field(default="v2.13.6", description="WAPI version")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    log_level: str = Field(default="INFO", description="Logging level")
    
    @validator('grid_master_ip')
    def validate_ip(cls, v):
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            # Could be hostname/FQDN
            if not v or len(v.strip()) == 0:
                raise ValueError("Grid Master IP cannot be empty")
            return v.strip()
    
    @validator('wapi_version')
    def validate_wapi_version(cls, v):
        """Validate WAPI version format."""
        if not v.startswith('v'):
            v = f"v{v}"
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class ConfigManager:
    """Manages InfoBlox MCP Server configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or Path.home() / ".infoblox-mcp"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "key.key"
        self._encryption_key = self._get_or_create_key()
        self._config: Optional[InfoBloxConfig] = None
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password."""
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password."""
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted_password.encode()).decode()
    
    def load_config(self) -> Optional[InfoBloxConfig]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Decrypt password
            if 'password' in config_data:
                config_data['password'] = self._decrypt_password(config_data['password'])
            
            self._config = InfoBloxConfig(**config_data)
            return self._config
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            return None
    
    def save_config(self, config: InfoBloxConfig) -> bool:
        """Save configuration to file."""
        try:
            config_data = config.dict()
            # Encrypt password before saving
            config_data['password'] = self._encrypt_password(config_data['password'])
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            self._config = config
            return True
        except Exception as e:
            click.echo(f"Error saving configuration: {e}", err=True)
            return False
    
    def prompt_for_config(self) -> InfoBloxConfig:
        """Prompt user for configuration."""
        click.echo("InfoBlox MCP Server Configuration")
        click.echo("=" * 40)
        
        # Grid Master IP
        grid_master_ip = click.prompt(
            "Grid Master IP address or hostname",
            type=str
        ).strip()
        
        # Username
        username = click.prompt(
            "InfoBlox username",
            type=str
        ).strip()
        
        # Password
        password = getpass.getpass("InfoBlox password: ")
        
        # Optional settings with defaults
        click.echo("\nOptional Settings (press Enter for defaults):")
        
        wapi_version = click.prompt(
            "WAPI version",
            default="v2.13.6",
            type=str
        )
        
        verify_ssl = click.confirm(
            "Verify SSL certificates?",
            default=True
        )
        
        timeout = click.prompt(
            "Request timeout (seconds)",
            default=30,
            type=int
        )
        
        max_retries = click.prompt(
            "Maximum retry attempts",
            default=3,
            type=int
        )
        
        log_level = click.prompt(
            "Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
            default="INFO",
            type=str
        )
        
        return InfoBloxConfig(
            grid_master_ip=grid_master_ip,
            username=username,
            password=password,
            wapi_version=wapi_version,
            verify_ssl=verify_ssl,
            timeout=timeout,
            max_retries=max_retries,
            log_level=log_level
        )
    
    def get_config(self) -> InfoBloxConfig:
        """Get configuration, prompting if necessary."""
        if self._config is None:
            self._config = self.load_config()
        
        if self._config is None:
            click.echo("No configuration found. Please provide InfoBlox connection details.")
            self._config = self.prompt_for_config()
            if not self.save_config(self._config):
                raise RuntimeError("Failed to save configuration")
        
        return self._config
    
    def update_config(self, **kwargs) -> bool:
        """Update configuration with new values."""
        if self._config is None:
            self._config = self.get_config()
        
        # Create updated config
        config_data = self._config.dict()
        config_data.update(kwargs)
        
        try:
            updated_config = InfoBloxConfig(**config_data)
            return self.save_config(updated_config)
        except Exception as e:
            click.echo(f"Error updating configuration: {e}", err=True)
            return False
    
    def reset_config(self) -> bool:
        """Reset configuration (delete config files)."""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            if self.key_file.exists():
                self.key_file.unlink()
            self._config = None
            return True
        except Exception as e:
            click.echo(f"Error resetting configuration: {e}", err=True)
            return False

