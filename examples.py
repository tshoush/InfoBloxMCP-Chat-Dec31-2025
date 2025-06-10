"""
InfoBlox MCP Server Usage Examples

This file contains practical examples of using the InfoBlox MCP Server
for common DNS, DHCP, and IPAM operations.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager
from infoblox_mcp.client import InfoBloxClient
from infoblox_mcp.tools import ToolRegistry


async def example_dns_operations():
    """Example DNS operations."""
    print("DNS Operations Examples")
    print("=" * 30)
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return
    
    registry = ToolRegistry()
    
    try:
        with InfoBloxClient(config) as client:
            # Example 1: List all DNS zones
            print("1. Listing DNS zones...")
            result = await registry.execute_tool("infoblox_dns_list_zones", {}, client)
            zones_data = json.loads(result)
            print(f"   Found {zones_data.get('count', 0)} zones")
            
            # Example 2: Create a new DNS zone
            print("2. Creating DNS zone 'example-test.com'...")
            zone_args = {
                "fqdn": "example-test.com",
                "comment": "Test zone created by MCP server"
            }
            result = await registry.execute_tool("infoblox_dns_create_zone", zone_args, client)
            print("   Zone creation result:", json.loads(result).get("success", False))
            
            # Example 3: Create A record
            print("3. Creating A record...")
            record_args = {
                "name": "server1.example-test.com",
                "ipv4addr": "192.168.1.100",
                "ttl": 3600,
                "comment": "Test server"
            }
            result = await registry.execute_tool("infoblox_dns_create_record_a", record_args, client)
            print("   A record creation result:", json.loads(result).get("success", False))
            
            # Example 4: Search for records
            print("4. Searching for A records...")
            search_args = {
                "record_type": "A",
                "name": "server1.example-test.com"
            }
            result = await registry.execute_tool("infoblox_dns_search_records", search_args, client)
            records_data = json.loads(result)
            print(f"   Found {records_data.get('count', 0)} matching records")
            
    except Exception as e:
        print(f"Error in DNS operations: {str(e)}")


async def example_dhcp_operations():
    """Example DHCP operations."""
    print("\nDHCP Operations Examples")
    print("=" * 30)
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return
    
    registry = ToolRegistry()
    
    try:
        with InfoBloxClient(config) as client:
            # Example 1: List DHCP networks
            print("1. Listing DHCP networks...")
            result = await registry.execute_tool("infoblox_dhcp_list_networks", {}, client)
            networks_data = json.loads(result)
            print(f"   Found {networks_data.get('count', 0)} networks")
            
            # Example 2: Create DHCP network
            print("2. Creating DHCP network...")
            network_args = {
                "network": "192.168.100.0/24",
                "comment": "Test network created by MCP server"
            }
            result = await registry.execute_tool("infoblox_dhcp_create_network", network_args, client)
            print("   Network creation result:", json.loads(result).get("success", False))
            
            # Example 3: Get next available IPs
            print("3. Getting next available IPs...")
            ip_args = {
                "network": "192.168.100.0/24",
                "num_ips": 5
            }
            result = await registry.execute_tool("infoblox_dhcp_get_next_available_ip", ip_args, client)
            ip_data = json.loads(result)
            available_ips = ip_data.get("available_ips", [])
            print(f"   Next available IPs: {', '.join(available_ips[:3])}...")
            
    except Exception as e:
        print(f"Error in DHCP operations: {str(e)}")


async def example_ipam_operations():
    """Example IPAM operations."""
    print("\nIPAM Operations Examples")
    print("=" * 30)
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return
    
    registry = ToolRegistry()
    
    try:
        with InfoBloxClient(config) as client:
            # Example 1: Get network utilization
            print("1. Getting network utilization...")
            util_args = {
                "network": "192.168.100.0/24"
            }
            result = await registry.execute_tool("infoblox_ipam_get_network_utilization", util_args, client)
            util_data = json.loads(result)
            print("   Network utilization data retrieved")
            
    except Exception as e:
        print(f"Error in IPAM operations: {str(e)}")


async def example_grid_operations():
    """Example Grid operations."""
    print("\nGrid Operations Examples")
    print("=" * 30)
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return
    
    registry = ToolRegistry()
    
    try:
        with InfoBloxClient(config) as client:
            # Example 1: List grid members
            print("1. Listing grid members...")
            result = await registry.execute_tool("infoblox_grid_list_members", {}, client)
            members_data = json.loads(result)
            print(f"   Found {members_data.get('count', 0)} grid members")
            
            # Example 2: Get grid status
            print("2. Getting grid status...")
            result = await registry.execute_tool("infoblox_grid_get_status", {}, client)
            status_data = json.loads(result)
            print(f"   Grid status: {status_data.get('status', 'unknown')}")
            
    except Exception as e:
        print(f"Error in Grid operations: {str(e)}")


async def example_bulk_operations():
    """Example bulk operations."""
    print("\nBulk Operations Examples")
    print("=" * 30)
    
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("No configuration found. Please run setup_config.py first.")
        return
    
    registry = ToolRegistry()
    
    try:
        with InfoBloxClient(config) as client:
            # Example 1: Bulk create A records
            print("1. Bulk creating A records...")
            bulk_records = [
                {"name": "host1.example-test.com", "ipv4addr": "192.168.100.10"},
                {"name": "host2.example-test.com", "ipv4addr": "192.168.100.11"},
                {"name": "host3.example-test.com", "ipv4addr": "192.168.100.12"}
            ]
            bulk_args = {
                "records": bulk_records,
                "view": "default"
            }
            result = await registry.execute_tool("infoblox_bulk_create_a_records", bulk_args, client)
            bulk_data = json.loads(result)
            print(f"   Bulk creation result: {bulk_data.get('success', False)}")
            
            # Example 2: Export to CSV
            print("2. Exporting data to CSV...")
            export_args = {
                "object_type": "record:a",
                "filename": "/tmp/exported_records.csv",
                "filters": {"zone": "example-test.com"}
            }
            result = await registry.execute_tool("infoblox_bulk_export_csv", export_args, client)
            export_data = json.loads(result)
            print(f"   Export result: {export_data.get('success', False)}")
            
    except Exception as e:
        print(f"Error in bulk operations: {str(e)}")


async def main():
    """Main example function."""
    print("InfoBlox MCP Server Usage Examples")
    print("=" * 40)
    print("Note: These examples require a configured InfoBlox connection.")
    print("Run 'python3 setup_config.py' first if you haven't configured the server.")
    print()
    
    # Run all examples
    await example_dns_operations()
    await example_dhcp_operations()
    await example_ipam_operations()
    await example_grid_operations()
    await example_bulk_operations()
    
    print("\n" + "=" * 40)
    print("Examples completed!")
    print("\nFor more information, see DOCUMENTATION.md")


if __name__ == "__main__":
    asyncio.run(main())

