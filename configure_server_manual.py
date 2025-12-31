
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager, InfoBloxConfig
from infoblox_mcp.client import InfoBloxClient

def setup_manual_config():
    print("Setting up InfoBlox configuration manually...")
    
    # Credentials provided by user
    config = InfoBloxConfig(
        grid_master_ip="192.168.1.224",
        username="admin",
        password="infoblox",
        wapi_version="v2.13.1",
        verify_ssl=False, # Usually safe default for internal labs, can be changed later
        timeout=30,
        max_retries=3,
        log_level="INFO"
    )
    
    manager = ConfigManager()
    
    # Try to save
    if manager.save_config(config):
        print(f"Configuration saved to: {manager.config_file}")
    else:
        print("Failed to save configuration.")
        return

    # Test connection
    print("\nTesting connection...")
    try:
        with InfoBloxClient(config) as client:
            if client.test_connection():
                print("✓ Connection successful!")
            else:
                print("✗ Connection failed (Network unreachable or invalid creds)")
                # We proceed anyway as asked, but warn
    except Exception as e:
         print(f"✗ Connection error: {e}")

if __name__ == "__main__":
    setup_manual_config()
