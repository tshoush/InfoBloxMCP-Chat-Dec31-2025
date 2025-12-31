
import sys
import os
import json
import logging
import urllib3

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from infoblox_mcp.config import ConfigManager
from infoblox_mcp.client import InfoBloxClient

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)

def verify_audit():
    try:
        config = ConfigManager().load_config()
        client = InfoBloxClient(config)
        
        print("Attempting to fetch audit logs...")
        # Get 1 recent audit log entry
        logs = client.get("auditlog", params={
            "_max_results": 1, 
            "_return_fields": "admin_name,timestamp,action,object_name,object_type"
        })
        
        print(f"Success! Retrieved {len(logs)} log entries.")
        if logs:
            print("Sample entry:")
            print(json.dumps(logs[0], indent=2))
        else:
            print("No audit logs found (empty).")
            
    except Exception as e:
        print(f"Error fetching audit logs: {e}")

if __name__ == "__main__":
    verify_audit()
