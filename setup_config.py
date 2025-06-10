"""Interactive configuration setup for InfoBlox MCP Server."""

import getpass
import ipaddress
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager, InfoBloxConfig
from infoblox_mcp.client import InfoBloxClient


def validate_ip_address(ip_str: str) -> bool:
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def get_user_input():
    """Get configuration input from user."""
    print("InfoBlox MCP Server Configuration Setup")
    print("=" * 45)
    print()
    
    # Get Grid Master IP
    while True:
        grid_master_ip = input("Enter InfoBlox Grid Master IP address: ").strip()
        if not grid_master_ip:
            print("Error: IP address cannot be empty")
            continue
        
        if not validate_ip_address(grid_master_ip):
            print("Error: Invalid IP address format")
            continue
        
        break
    
    # Get username
    while True:
        username = input("Enter InfoBlox username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            continue
        break
    
    # Get password
    while True:
        password = getpass.getpass("Enter InfoBlox password: ")
        if not password:
            print("Error: Password cannot be empty")
            continue
        break
    
    # Get optional settings
    print("\nOptional Settings (press Enter for defaults):")
    
    wapi_version = input("WAPI version [v2.12]: ").strip() or "v2.12"
    
    verify_ssl_input = input("Verify SSL certificates? [y/N]: ").strip().lower()
    verify_ssl = verify_ssl_input in ['y', 'yes', 'true', '1']
    
    timeout_input = input("Request timeout in seconds [30]: ").strip()
    try:
        timeout = int(timeout_input) if timeout_input else 30
    except ValueError:
        timeout = 30
    
    max_retries_input = input("Maximum retries [3]: ").strip()
    try:
        max_retries = int(max_retries_input) if max_retries_input else 3
    except ValueError:
        max_retries = 3
    
    log_level = input("Log level [INFO]: ").strip().upper() or "INFO"
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        log_level = "INFO"
    
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


def test_connection(config: InfoBloxConfig) -> bool:
    """Test connection with the provided configuration."""
    print("\nTesting connection to InfoBlox...")
    
    try:
        with InfoBloxClient(config) as client:
            if client.test_connection():
                print("✓ Connection test successful!")
                return True
            else:
                print("✗ Connection test failed")
                return False
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
        return False


def main():
    """Main configuration setup function."""
    config_manager = ConfigManager()
    
    # Check if configuration already exists
    existing_config = config_manager.load_config()
    if existing_config:
        print(f"Existing configuration found for Grid Master: {existing_config.grid_master_ip}")
        overwrite = input("Do you want to overwrite the existing configuration? [y/N]: ").strip().lower()
        if overwrite not in ['y', 'yes', 'true', '1']:
            print("Configuration setup cancelled.")
            return
    
    # Get new configuration
    config = get_user_input()
    
    # Test connection
    if test_connection(config):
        # Save configuration
        if config_manager.save_config(config):
            print("\n✓ Configuration saved successfully!")
            print(f"Configuration file: {config_manager.config_file}")
            print("\nYou can now run the InfoBlox MCP Server:")
            print("  python3 infoblox-mcp-server.py")
        else:
            print("\n✗ Failed to save configuration")
            sys.exit(1)
    else:
        print("\nConnection test failed. Please check your settings and try again.")
        retry = input("Do you want to retry configuration? [y/N]: ").strip().lower()
        if retry in ['y', 'yes', 'true', '1']:
            main()  # Recursive retry
        else:
            print("Configuration setup cancelled.")
            sys.exit(1)


if __name__ == "__main__":
    main()

