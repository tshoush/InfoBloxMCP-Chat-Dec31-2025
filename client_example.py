
import asyncio
import json
import sys
import os
import tempfile

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager
from infoblox_mcp.client import InfoBloxClient
from infoblox_mcp.tools import ToolRegistry

import argparse

async def main():
    parser = argparse.ArgumentParser(description="InfoBlox AWS Import Client Example")
    parser.add_argument("--file", help="Path to AWS PVC export CSV file")
    parser.add_argument("--execute", action="store_true", help="Execute import (default is analysis only)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run execution in dry-run mode (default: True)")
    
    args = parser.parse_args()

    print("InfoBlox AWS Import Client Example")
    print("=" * 40)
    
    # 1. Load Configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return

    # 2. Determine Input File
    if args.file:
        file_path = args.file
        if not os.path.exists(file_path):
             print(f"Error: File not found at {file_path}")
             return
        print(f"Using input file: {file_path}")
        temp_file_created = False
    else:
        # Create a sample AWS Export file for demonstration
        sample_csv_content = """AccountId,Region,VpcId,Name,CidrBlock,Tags
111,us-east-1,vpc-1,DemoVPC,10.212.224.0/23,"[{'Key': 'Owner', 'Value': 'DemoUser'}, {'Key': 'Environment', 'Value': 'Staging'}]"
222,us-east-1,vpc-2,DemoVPC2,192.168.99.0/24,"[{'Key': 'Project', 'Value': 'Migration'}]"
"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
            temp_file.write(sample_csv_content)
            file_path = temp_file.name
        
        print(f"Created sample file at: {file_path}")
        temp_file_created = True

    try:
        # 3. Initialize Registry and Client
        registry = ToolRegistry()
        
        # 4. Connect and Execute
        with InfoBloxClient(config) as client:
            
            tool_name = "infoblox_aws_import_analysis"
            tool_args = {"file_name": file_path}

            if args.execute:
                tool_name = "infoblox_aws_import_execute"
                tool_args["dry_run"] = args.dry_run
                print(f"\nExecuting IMPORT tool (dry_run={args.dry_run})...")
            else:
                print("\nExecuting ANALYSIS tool...")
            
            # Execute the tool
            result_json = await registry.execute_tool(tool_name, tool_args, client)
            
            # 5. Process Results
            result = json.loads(result_json)
            
            print("\nResults:")
            print("-" * 20)
            print(json.dumps(result, indent=2))
            
            # Simple summary handling that works for both tools (if structure matches)
            if "total_records" in result:
                print("\nSummary:")
                print(f"Total Records: {result.get('total_records')}")
                print(f"Valid Records: {result.get('valid_records')}")
                print(f"Conflicts: {len(result.get('conflicts', []))}")
                if "missing_eas" in result:
                    print(f"Missing EAs: {len(result.get('missing_eas', []))}")
                if "created_networks" in result:
                     print(f"Created Networks: {len(result.get('created_networks', []))}")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
    
    finally:
        # Cleanup if we created a temp file
        if temp_file_created and os.path.exists(file_path):
            os.remove(file_path)
            print(f"\nCleaned up sample file.")

if __name__ == "__main__":
    asyncio.run(main())
