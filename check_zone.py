
import asyncio
import sys
import os
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager
from infoblox_mcp.client import InfoBloxClient

async def check_zone():
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found.")
        return

    print("Checking for zone 'marriott.com'...")
    try:
        with InfoBloxClient(config) as client:
            # Search audit log for creation of this zone
            logs = client.search_objects("auditlog", {
                "object_type": "zone_auth",
                "object_name": "marriott.com", 
                "opcode": "CREATE"
            })
            
            if logs:
                print(f"Found creation log!")
                print(json.dumps(logs[0], indent=2))
            else:
                print("No creation log found for 'marriott.com'.")
                
    except Exception as e:
        print(f"Error searching for zone: {e}")

if __name__ == "__main__":
    asyncio.run(check_zone())
