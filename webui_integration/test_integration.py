#!/usr/bin/env python3
"""
Test script for InfoBlox Open WebUI Integration

This script tests the integration components to ensure everything works correctly.
"""

import asyncio
import os
import sys
import json
import logging
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Test suite for InfoBlox Open WebUI integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = []
        self.setup_environment()
    
    def setup_environment(self):
        """Setup test environment."""
        # Set default MCP server path if not set
        if not os.getenv("INFOBLOX_MCP_SERVER_PATH"):
            os.environ["INFOBLOX_MCP_SERVER_PATH"] = "python3 infoblox-mcp-server.py"
        
        logger.info("Test environment setup complete")
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if message:
            logger.info(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    async def test_intent_recognition(self):
        """Test intent recognition functionality."""
        logger.info("Testing intent recognition...")
        
        try:
            from infoblox_function import InfoBloxWebUIFunction
            func = InfoBloxWebUIFunction()
            
            # Test cases
            test_cases = [
                ("show network 192.168.1.0/24 utilization", "infoblox_ipam_get_network_utilization"),
                ("list DNS zones", "infoblox_dns_list_zones"),
                ("get next available IPs in 10.0.0.0/24", "infoblox_dhcp_get_next_available_ip"),
                ("show DHCP networks", "infoblox_dhcp_list_networks"),
                ("list grid members", "infoblox_grid_list_members"),
            ]
            
            passed = 0
            for query, expected_tool in test_cases:
                result = func.recognize_intent(query)
                if result and result[0] == expected_tool:
                    passed += 1
                    logger.info(f"  ✅ '{query}' → {result[0]}")
                else:
                    logger.warning(f"  ❌ '{query}' → {result}")
            
            success = passed == len(test_cases)
            self.log_test_result(
                "Intent Recognition", 
                success, 
                f"{passed}/{len(test_cases)} test cases passed"
            )
            
        except Exception as e:
            self.log_test_result("Intent Recognition", False, str(e))
    
    async def test_llm_configuration(self):
        """Test LLM configuration."""
        logger.info("Testing LLM configuration...")
        
        try:
            from infoblox_function import InfoBloxWebUIFunction
            func = InfoBloxWebUIFunction()
            
            available_providers = len(func.llm_configs)
            
            if available_providers > 0:
                providers = [config["provider"] for config in func.llm_configs]
                self.log_test_result(
                    "LLM Configuration", 
                    True, 
                    f"Found {available_providers} providers: {', '.join(providers)}"
                )
            else:
                self.log_test_result(
                    "LLM Configuration", 
                    False, 
                    "No LLM API keys configured"
                )
                
        except Exception as e:
            self.log_test_result("LLM Configuration", False, str(e))
    
    async def test_mcp_server_connection(self):
        """Test MCP server connection."""
        logger.info("Testing MCP server connection...")
        
        try:
            # Try to import InfoBlox MCP components
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
            
            from infoblox_mcp.config import ConfigManager
            from infoblox_mcp.client import InfoBloxClient
            
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            if config:
                try:
                    with InfoBloxClient(config) as client:
                        if client.test_connection():
                            self.log_test_result(
                                "MCP Server Connection", 
                                True, 
                                f"Connected to {config.grid_master_ip}"
                            )
                        else:
                            self.log_test_result(
                                "MCP Server Connection", 
                                False, 
                                "Connection test failed"
                            )
                except Exception as e:
                    self.log_test_result(
                        "MCP Server Connection", 
                        False, 
                        f"Connection error: {str(e)}"
                    )
            else:
                self.log_test_result(
                    "MCP Server Connection", 
                    False, 
                    "InfoBlox MCP server not configured"
                )
                
        except ImportError as e:
            self.log_test_result(
                "MCP Server Connection", 
                False, 
                f"Cannot import MCP components: {str(e)}"
            )
        except Exception as e:
            self.log_test_result("MCP Server Connection", False, str(e))
    
    async def test_response_formatting(self):
        """Test response formatting."""
        logger.info("Testing response formatting...")
        
        try:
            from infoblox_function import InfoBloxWebUIFunction
            func = InfoBloxWebUIFunction()
            
            # Test utilization formatting
            test_data = {
                "network": "192.168.1.0/24",
                "utilization": {
                    "utilization_percent": 75.5,
                    "used_ips": 192,
                    "total_ips": 254
                }
            }
            
            formatted = func._format_utilization(test_data)
            
            if "📊 Network Utilization" in formatted and "75.5%" in formatted:
                self.log_test_result("Response Formatting", True, "Utilization formatting works")
            else:
                self.log_test_result("Response Formatting", False, "Utilization formatting failed")
                
        except Exception as e:
            self.log_test_result("Response Formatting", False, str(e))
    
    async def test_end_to_end_query(self):
        """Test end-to-end query processing."""
        logger.info("Testing end-to-end query processing...")
        
        try:
            from infoblox_function import infoblox_query
            
            # Test with a simple query that should work with intent recognition
            test_query = "list grid members"
            
            result = await infoblox_query(test_query)
            
            if "❌" not in result and "❓" not in result:
                self.log_test_result(
                    "End-to-End Query", 
                    True, 
                    f"Query '{test_query}' processed successfully"
                )
            else:
                self.log_test_result(
                    "End-to-End Query", 
                    False, 
                    f"Query failed: {result[:100]}..."
                )
                
        except Exception as e:
            self.log_test_result("End-to-End Query", False, str(e))
    
    async def test_environment_variables(self):
        """Test environment variable configuration."""
        logger.info("Testing environment variables...")
        
        required_vars = ["INFOBLOX_MCP_SERVER_PATH"]
        optional_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY"]
        
        missing_required = []
        available_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if os.getenv(var):
                available_optional.append(var)
        
        if missing_required:
            self.log_test_result(
                "Environment Variables", 
                False, 
                f"Missing required variables: {', '.join(missing_required)}"
            )
        else:
            self.log_test_result(
                "Environment Variables", 
                True, 
                f"Required variables set. Optional: {', '.join(available_optional) if available_optional else 'None'}"
            )
    
    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*60)
        
        if passed_tests < total_tests:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['message']}")
        
        print("\nRECOMMENDATIONS:")
        
        # Check for common issues
        has_llm = any("LLM" in result["test"] and result["success"] for result in self.test_results)
        has_mcp = any("MCP" in result["test"] and result["success"] for result in self.test_results)
        
        if not has_llm:
            print("• Set at least one LLM API key for fallback functionality")
            print("  export OPENAI_API_KEY='your-key'")
        
        if not has_mcp:
            print("• Ensure InfoBlox MCP server is running and configured")
            print("  python3 setup_config.py")
            print("  python3 infoblox-mcp-server.py --test-connection")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! The integration is ready to use.")
        elif passed_tests >= total_tests * 0.7:
            print("⚠️  Most tests passed. Address the failed tests for full functionality.")
        else:
            print("🚨 Many tests failed. Check configuration and dependencies.")


async def main():
    """Main test function."""
    print("InfoBlox Open WebUI Integration Test Suite")
    print("="*60)
    
    tester = IntegrationTester()
    
    # Run all tests
    await tester.test_environment_variables()
    await tester.test_intent_recognition()
    await tester.test_llm_configuration()
    await tester.test_response_formatting()
    await tester.test_mcp_server_connection()
    await tester.test_end_to_end_query()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
