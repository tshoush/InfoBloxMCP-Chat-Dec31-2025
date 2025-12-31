"""Comprehensive test suite for InfoBlox MCP Server."""

import asyncio
import json
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager, InfoBloxConfig
from infoblox_mcp.client import InfoBloxClient, InfoBloxAPIError
from infoblox_mcp.tools import ToolRegistry
from infoblox_mcp.error_handling import (
    setup_logging, validate_ip_address, validate_network_cidr,
    validate_hostname, validate_mac_address, sanitize_input
)


class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def pass_test(self, test_name: str):
        """Record a passed test."""
        print(f"✓ {test_name}")
        self.passed += 1
    
    def fail_test(self, test_name: str, error: str):
        """Record a failed test."""
        print(f"✗ {test_name}: {error}")
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
    
    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\nTest Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print("Failed tests:")
            for error in self.errors:
                print(f"  - {error}")


async def test_configuration_management(results: TestResults):
    """Test configuration management."""
    print("Testing Configuration Management...")
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            config_manager = ConfigManager(Path(temp_dir))
            
            # Test saving and loading configuration
            test_config = InfoBloxConfig(
                grid_master_ip="192.168.1.100",
                username="admin",
                password="password123",
                wapi_version="v2.12",
                verify_ssl=False,
                timeout=30,
                max_retries=3,
                log_level="INFO"
            )
            
            # Save config
            if config_manager.save_config(test_config):
                results.pass_test("Configuration saving")
            else:
                results.fail_test("Configuration saving", "Failed to save")
            
            # Load config
            loaded_config = config_manager.load_config()
            if loaded_config and loaded_config.grid_master_ip == "192.168.1.100":
                results.pass_test("Configuration loading")
            else:
                results.fail_test("Configuration loading", "Failed to load or data mismatch")
            
            # Test reset
            if config_manager.reset_config():
                results.pass_test("Configuration reset")
            else:
                results.fail_test("Configuration reset", "Failed to reset")
            
        except Exception as e:
            results.fail_test("Configuration management", str(e))


async def test_validation_functions(results: TestResults):
    """Test validation functions."""
    print("Testing Validation Functions...")
    
    # Test IP address validation
    valid_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "2001:db8::1"]
    invalid_ips = ["256.256.256.256", "192.168.1", "not.an.ip", ""]
    
    for ip in valid_ips:
        if validate_ip_address(ip):
            results.pass_test(f"Valid IP validation: {ip}")
        else:
            results.fail_test(f"Valid IP validation: {ip}", "Should be valid")
    
    for ip in invalid_ips:
        if not validate_ip_address(ip):
            results.pass_test(f"Invalid IP validation: {ip}")
        else:
            results.fail_test(f"Invalid IP validation: {ip}", "Should be invalid")
    
    # Test network CIDR validation
    valid_networks = ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/16"]
    invalid_networks = ["192.168.1.0/33", "not.a.network", "192.168.1.0"]
    
    for network in valid_networks:
        if validate_network_cidr(network):
            results.pass_test(f"Valid network validation: {network}")
        else:
            results.fail_test(f"Valid network validation: {network}", "Should be valid")
    
    for network in invalid_networks:
        if not validate_network_cidr(network):
            results.pass_test(f"Invalid network validation: {network}")
        else:
            results.fail_test(f"Invalid network validation: {network}", "Should be invalid")
    
    # Test hostname validation
    valid_hostnames = ["example.com", "test.example.com", "host-1.domain.org"]
    invalid_hostnames = ["", "a" * 300, "invalid..domain", "-invalid.com"]
    
    for hostname in valid_hostnames:
        if validate_hostname(hostname):
            results.pass_test(f"Valid hostname validation: {hostname}")
        else:
            results.fail_test(f"Valid hostname validation: {hostname}", "Should be valid")
    
    for hostname in invalid_hostnames:
        if not validate_hostname(hostname):
            results.pass_test(f"Invalid hostname validation: {hostname}")
        else:
            results.fail_test(f"Invalid hostname validation: {hostname}", "Should be invalid")
    
    # Test MAC address validation
    valid_macs = ["00:11:22:33:44:55", "00-11-22-33-44-55", "0011.2233.4455", "001122334455"]
    invalid_macs = ["00:11:22:33:44", "GG:11:22:33:44:55", "not.a.mac"]
    
    for mac in valid_macs:
        if validate_mac_address(mac):
            results.pass_test(f"Valid MAC validation: {mac}")
        else:
            results.fail_test(f"Valid MAC validation: {mac}", "Should be valid")
    
    for mac in invalid_macs:
        if not validate_mac_address(mac):
            results.pass_test(f"Invalid MAC validation: {mac}")
        else:
            results.fail_test(f"Invalid MAC validation: {mac}", "Should be invalid")


async def test_tool_registry(results: TestResults):
    """Test tool registry functionality."""
    print("Testing Tool Registry...")
    
    try:
        registry = ToolRegistry()
        
        # Test tool registration
        tools = registry.get_all_tools()
        if len(tools) > 0:
            results.pass_test(f"Tool registration ({len(tools)} tools)")
        else:
            results.fail_test("Tool registration", "No tools registered")
        
        # Test tool categories
        expected_categories = ['dns', 'dhcp', 'ipam', 'grid', 'bulk']
        found_categories = set()
        
        for tool in tools:
            if '_' in tool.name:
                category = tool.name.split('_')[1]
                found_categories.add(category)
        
        for category in expected_categories:
            if category in found_categories:
                results.pass_test(f"Tool category: {category}")
            else:
                results.fail_test(f"Tool category: {category}", "Category not found")
        
        # Test specific tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'infoblox_dns_list_zones',
            'infoblox_dns_create_zone',
            'infoblox_dhcp_list_networks',
            'infoblox_dhcp_create_network',
            'infoblox_grid_list_members',
            'infoblox_aws_import_analysis',
            'infoblox_splunk_audit_search'
        ]
        
        for tool_name in expected_tools:
            if tool_name in tool_names:
                results.pass_test(f"Tool exists: {tool_name}")
            else:
                results.fail_test(f"Tool exists: {tool_name}", "Tool not found")
        
    except Exception as e:
        results.fail_test("Tool registry", str(e))


async def test_error_handling(results: TestResults):
    """Test error handling functionality."""
    print("Testing Error Handling...")
    
    try:
        # Test input sanitization
        test_inputs = [
            ("normal text", "normal text"),
            ("text with\x00control\x01chars", "text withcontrolchars"),
            ("a" * 300, "a" * 255),  # Should be truncated
            ("  spaced text  ", "spaced text")  # Should be trimmed
        ]
        
        for input_text, expected in test_inputs:
            sanitized = sanitize_input(input_text)
            if sanitized == expected:
                results.pass_test(f"Input sanitization: '{input_text[:20]}...'")
            else:
                results.fail_test(f"Input sanitization: '{input_text[:20]}...'", 
                                 f"Expected '{expected}', got '{sanitized}'")
        
        # Test logging setup
        logger = setup_logging("DEBUG")
        if logger and logger.level == 10:  # DEBUG level
            results.pass_test("Logging setup")
        else:
            results.fail_test("Logging setup", "Logger not configured correctly")
        
    except Exception as e:
        results.fail_test("Error handling", str(e))


async def test_mock_client_operations(results: TestResults):
    """Test client operations with mocked responses."""
    print("Testing Mock Client Operations...")
    
    try:
        # Create a mock config
        config = InfoBloxConfig(
            grid_master_ip="192.168.1.100",
            username="admin",
            password="password123"
        )
        
        # Mock the requests session
        with patch('requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"_ref": "grid/b25lLmNsdXN0ZXIkMA:Infoblox"}]
            mock_response.cookies = {'ibapauth': 'test_cookie'}
            
            mock_session.return_value.get.return_value = mock_response
            mock_session.return_value.post.return_value = mock_response
            mock_session.return_value.put.return_value = mock_response
            mock_session.return_value.get.return_value = mock_response
            mock_session.return_value.post.return_value = mock_response
            mock_session.return_value.put.return_value = mock_response
            mock_session.return_value.delete.return_value = mock_response
            mock_session.return_value.request.return_value = mock_response
            
            # Test client initialization
            client = InfoBloxClient(config)
            results.pass_test("Client initialization")
            
            # Test basic operations
            result = client.get("grid")
            if isinstance(result, list) and len(result) > 0:
                results.pass_test("Mock GET operation")
            else:
                results.fail_test("Mock GET operation", "Unexpected response")
            
            # Test tool execution with mock client
            registry = ToolRegistry()
            
            # Mock a simple tool execution
            mock_result = await registry.execute_tool("infoblox_grid_list_members", {}, client)
            if mock_result and "members" in mock_result:
                results.pass_test("Mock tool execution")
            else:
                results.fail_test("Mock tool execution", "Unexpected result")
        
    except Exception as e:
        results.fail_test("Mock client operations", str(e))


async def test_server_initialization(results: TestResults):
    """Test MCP server initialization."""
    print("Testing Server Initialization...")
    
    try:
        from infoblox_mcp.server import InfoBloxMCPServer
        
        # Test server creation
        server = InfoBloxMCPServer()
        if server:
            results.pass_test("Server initialization")
        else:
            results.fail_test("Server initialization", "Failed to create server")
        
        # Test tool registry in server
        if server.tool_registry and len(server.tool_registry.tools) > 0:
            results.pass_test("Server tool registry")
        else:
            results.fail_test("Server tool registry", "No tools in registry")
        
    except Exception as e:
        results.fail_test("Server initialization", str(e))


async def main():
    """Main test function."""
    print("InfoBlox MCP Server Comprehensive Test Suite")
    print("=" * 50)
    
    results = TestResults()
    
    # Run all test suites
    await test_configuration_management(results)
    await test_validation_functions(results)
    await test_tool_registry(results)
    await test_error_handling(results)
    await test_mock_client_operations(results)
    await test_server_initialization(results)
    
    print("\n" + "=" * 50)
    results.summary()
    
    # Return exit code based on results
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

