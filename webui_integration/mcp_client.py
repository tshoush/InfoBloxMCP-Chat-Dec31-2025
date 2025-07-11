"""
MCP Client Wrapper for InfoBlox MCP Server Integration

This module provides a client interface to communicate with the InfoBlox MCP server
and execute tools programmatically.
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class MCPToolInfo:
    """Information about an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str


@dataclass
class MCPResponse:
    """Response from MCP tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time: Optional[float] = None


class InfoBloxMCPClient:
    """Client for communicating with InfoBlox MCP Server."""
    
    def __init__(self, mcp_server_path: str = None):
        """
        Initialize the MCP client.
        
        Args:
            mcp_server_path: Path to the InfoBlox MCP server script
        """
        self.mcp_server_path = mcp_server_path or "python3 infoblox-mcp-server.py"
        self.tools_cache: Optional[List[MCPToolInfo]] = None
        self._server_process: Optional[subprocess.Popen] = None
        
    async def start_server(self) -> bool:
        """Start the MCP server process."""
        try:
            # Start the MCP server as a subprocess
            self._server_process = subprocess.Popen(
                self.mcp_server_path.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Wait a moment for server to initialize
            await asyncio.sleep(2)
            
            # Check if process is still running
            if self._server_process.poll() is None:
                logger.info("MCP server started successfully")
                return True
            else:
                logger.error("MCP server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server: {str(e)}")
            return False
    
    async def stop_server(self):
        """Stop the MCP server process."""
        if self._server_process:
            self._server_process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process()), 
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self._server_process.kill()
            self._server_process = None
            logger.info("MCP server stopped")
    
    async def _wait_for_process(self):
        """Wait for the process to terminate."""
        while self._server_process and self._server_process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        if not self._server_process:
            raise RuntimeError("MCP server not started")
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self._server_process.stdin.write(request_json)
            self._server_process.stdin.flush()
            
            # Read response
            response_line = self._server_process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response from MCP server")
            
            return json.loads(response_line.strip())
            
        except Exception as e:
            logger.error(f"MCP communication error: {str(e)}")
            raise
    
    async def list_tools(self) -> List[MCPToolInfo]:
        """Get list of available tools from the MCP server."""
        if self.tools_cache:
            return self.tools_cache
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            response = await self.send_mcp_request(request)
            
            if "result" in response and "tools" in response["result"]:
                tools = []
                for tool_data in response["result"]["tools"]:
                    # Extract category from tool name
                    category = "unknown"
                    if "_" in tool_data["name"]:
                        parts = tool_data["name"].split("_")
                        if len(parts) > 1:
                            category = parts[1]
                    
                    tool = MCPToolInfo(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("inputSchema", {}).get("properties", {}),
                        category=category
                    )
                    tools.append(tool)
                
                self.tools_cache = tools
                return tools
            else:
                logger.error("Invalid response format for tools/list")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            return []
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Execute a specific tool with given arguments."""
        import time
        start_time = time.time()
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self.send_mcp_request(request)
            execution_time = time.time() - start_time
            
            if "result" in response:
                # Extract content from MCP response
                result_data = response["result"]
                if isinstance(result_data, list) and len(result_data) > 0:
                    content = result_data[0].get("text", "")
                    try:
                        # Try to parse as JSON
                        parsed_data = json.loads(content)
                        return MCPResponse(
                            success=True,
                            data=parsed_data,
                            tool_name=tool_name,
                            execution_time=execution_time
                        )
                    except json.JSONDecodeError:
                        # Return as plain text
                        return MCPResponse(
                            success=True,
                            data=content,
                            tool_name=tool_name,
                            execution_time=execution_time
                        )
                else:
                    return MCPResponse(
                        success=True,
                        data=result_data,
                        tool_name=tool_name,
                        execution_time=execution_time
                    )
            
            elif "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                return MCPResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    tool_name=tool_name,
                    execution_time=execution_time
                )
            
            else:
                return MCPResponse(
                    success=False,
                    data=None,
                    error="Invalid response format",
                    tool_name=tool_name,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool execution failed: {str(e)}")
            return MCPResponse(
                success=False,
                data=None,
                error=str(e),
                tool_name=tool_name,
                execution_time=execution_time
            )
    
    async def get_tools_by_category(self, category: str) -> List[MCPToolInfo]:
        """Get tools filtered by category."""
        tools = await self.list_tools()
        return [tool for tool in tools if tool.category.lower() == category.lower()]
    
    async def search_tools(self, query: str) -> List[MCPToolInfo]:
        """Search tools by name or description."""
        tools = await self.list_tools()
        query_lower = query.lower()
        
        matching_tools = []
        for tool in tools:
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        return matching_tools
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_server()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_server()


# Convenience functions for common operations
async def get_network_utilization(network: str) -> MCPResponse:
    """Get network utilization for a specific network."""
    async with InfoBloxMCPClient() as client:
        return await client.execute_tool(
            "infoblox_ipam_get_network_utilization",
            {"network": network}
        )


async def list_dns_zones() -> MCPResponse:
    """List all DNS zones."""
    async with InfoBloxMCPClient() as client:
        return await client.execute_tool("infoblox_dns_list_zones", {})


async def list_dhcp_networks() -> MCPResponse:
    """List all DHCP networks."""
    async with InfoBloxMCPClient() as client:
        return await client.execute_tool("infoblox_dhcp_list_networks", {})
