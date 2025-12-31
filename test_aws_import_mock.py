
import asyncio
import json
import logging
import sys
import os
import tempfile
from unittest.mock import MagicMock

# Add src to path so we can import internal modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.additional_tools import AnalysisTools

# Configure logging to show what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_aws_import_logic():
    print("Running AWS Import Analysis Test (Mocked)")
    print("=" * 40)
    
    # 1. Mock the InfoBlox Client
    # This simulates the InfoBlox server so you don't need a real connection
    mock_client = MagicMock()
    
    # Define what EAs exist in our "Mocked" InfoBlox
    valid_eas = {"Owner", "Environment", "CostCenter", "AccountId", "Name"}
    
    # Define what Networks exist in our "Mocked" InfoBlox
    existing_networks = {"10.212.224.0/23"}

    def mock_search_objects(object_type, params=None):
        if object_type == "extensibleattributedef":
            return [{"name": ea} for ea in valid_eas]
        elif object_type == "network":
            network = params.get("network")
            if network in existing_networks:
                 return [{"_ref": f"network/ZG5Td...:{network}/default"}]
            return []
        return []

    mock_client.search_objects = MagicMock(side_effect=mock_search_objects)

    # 2. Create a temporary CSV file with test data
    # Row 1: Should conflict (network exists) and have valid EAs
    # Row 2: Should match but have a missing EA (UnknownTag)
    test_csv_content = """AccountId,Region,VpcId,Name,CidrBlock,Tags
111,us-east-1,vpc-1,TestVPC,10.212.224.0/23,"[{'Key': 'Owner', 'Value': 'Me'}, {'Key': 'Environment', 'Value': 'Prod'}]"
222,us-east-1,vpc-2,TestVPC2,192.168.1.0/24,"[{'Key': 'UnknownTag', 'Value': 'Value'}]"
"""
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
        temp_file.write(test_csv_content)
        temp_file_path = temp_file.name

    print(f"Created temporary test file: {temp_file_path}")
    print("-" * 20)
    print("Test Data Preview:")
    print(test_csv_content)
    print("-" * 20)

    try:
        # 3. Run the tool
        print("Executing tool logic...")
        args = {"file_name": temp_file_path}
        
        # We call the internal method directly since we are mocking the client
        result_json = await AnalysisTools._aws_import_analysis(args, mock_client)
        result = json.loads(result_json)
        
        # 4. Show Results
        print("\nAnalysis Results:")
        print(json.dumps(result, indent=2))
        
        # 5. Verify expectations
        print("\nVerifying results...")
        
        # Check Conflict
        if any(c['network'] == '10.212.224.0/23' for c in result['conflicts']):
            print("✅ Correctly identified conflict for 10.212.224.0/23")
        else:
            print("❌ Failed to identify conflict for 10.212.224.0/23")

        # Check Missing EA
        if "UnknownTag" in result['missing_eas']:
             print("✅ Correctly identified 'UnknownTag' as missing EA")
        else:
             print("❌ Failed to identify 'UnknownTag'")

        # Check Mapped EAs
        if "Owner" in result['mapped_eas'] and "AccountId" in result['mapped_eas']:
            print("✅ Correctly mapped valid EAs (Owner, AccountId)")
        else:
            print("❌ Failed to map valid EAs")

    except Exception as e:
        print(f"\nTest Failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    asyncio.run(test_aws_import_logic())
