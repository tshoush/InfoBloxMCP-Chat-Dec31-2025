"""Test script for InfoBlox MCP Server functionality."""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager, InfoBloxConfig
from infoblox_mcp.client import InfoBloxClient, InfoBloxAPIError
from infoblox_mcp.tools import ToolRegistry


async def test_configuration():
    """Test configuration management."""
    print("Testing configuration management...")
    
    config_manager = ConfigManager()
    
    # Test if config exists
    config = config_manager.load_config()
    if config is None:
        print("No configuration found. This is expected for first run.")
        return False
    else:
        print(f"Configuration loaded: Grid Master = {config.grid_master_ip}")
        return True


async def test_client_connection(config: InfoBloxConfig):
    """Test InfoBlox client connection."""
    print("Testing InfoBlox client connection...")
    
    try:
        with InfoBloxClient(config) as client:
            if client.test_connection():
                print("✓ Connection test successful")
                return True
            else:
                print("✗ Connection test failed")
                return False
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
        return False


async def test_tools():
    """Test tool registry."""
    print("Testing tool registry...")
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    print(f"✓ Registered {len(tools)} tools:")
    
    # Group tools by category
    categories = {}
    for tool in tools:
        category = tool.name.split('_')[1] if '_' in tool.name else 'other'
        if category not in categories:
            categories[category] = []
        categories[category].append(tool.name)
    
    for category, tool_names in categories.items():
        print(f"  {category.upper()}: {len(tool_names)} tools")
        for tool_name in sorted(tool_names)[:3]:  # Show first 3 tools
            print(f"    - {tool_name}")
        if len(tool_names) > 3:
            print(f"    ... and {len(tool_names) - 3} more")
    
    return True


async def test_basic_operations(config: InfoBloxConfig):
    """Test basic InfoBlox operations."""
    print("Testing basic InfoBlox operations...")
    
    try:
        registry = ToolRegistry()
        
        with InfoBloxClient(config) as client:
            # Test listing grid members
            print("  Testing grid member listing...")
            result = await registry.execute_tool("infoblox_grid_list_members", {}, client)
            data = json.loads(result)
            print(f"  ✓ Found {data.get('count', 0)} grid members")
            
            # Test listing DNS zones
            print("  Testing DNS zone listing...")
            result = await registry.execute_tool("infoblox_dns_list_zones", {}, client)
            data = json.loads(result)
            print(f"  ✓ Found {data.get('count', 0)} DNS zones")
            
            # Test listing DHCP networks
            print("  Testing DHCP network listing...")
            result = await registry.execute_tool("infoblox_dhcp_list_networks", {}, client)
            data = json.loads(result)
            print(f"  ✓ Found {data.get('count', 0)} DHCP networks")
            
            return True
            
    except Exception as e:
        print(f"  ✗ Basic operations test failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("InfoBlox MCP Server Test Suite")
    print("=" * 40)
    
    # Test configuration
    config_exists = await test_configuration()
    
    # Test tool registry
    await test_tools()
    
    if config_exists:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Test client connection
        connection_ok = await test_client_connection(config)
        
        if connection_ok:
            # Test basic operations
            await test_basic_operations(config)
    else:
        print("\nSkipping connection and operation tests (no configuration)")
    
    print("\n" + "=" * 40)
    print("Test suite completed")


if __name__ == "__main__":
    asyncio.run(main())

