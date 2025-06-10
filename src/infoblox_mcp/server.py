"""MCP Server implementation for InfoBlox DDI."""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
import mcp.types as types

from .config import ConfigManager, InfoBloxConfig
from .client import InfoBloxClient, InfoBloxAPIError
from .tools import ToolRegistry


logger = logging.getLogger(__name__)


class InfoBloxMCPServer:
    """InfoBlox MCP Server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.config_manager = ConfigManager()
        self.config: Optional[InfoBloxConfig] = None
        self.client: Optional[InfoBloxClient] = None
        self.tool_registry = ToolRegistry()
        self.server = Server("infoblox-mcp-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="infoblox://config",
                    name="InfoBlox Configuration",
                    description="Current InfoBlox connection configuration",
                    mimeType="application/json"
                ),
                Resource(
                    uri="infoblox://status",
                    name="Connection Status",
                    description="InfoBlox connection and system status",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource."""
            if uri == "infoblox://config":
                if self.config:
                    config_data = self.config.dict()
                    # Don't expose password
                    config_data.pop('password', None)
                    return json.dumps(config_data, indent=2)
                return json.dumps({"error": "No configuration loaded"})
            
            elif uri == "infoblox://status":
                status = {
                    "configured": self.config is not None,
                    "connected": False,
                    "grid_master": None,
                    "wapi_version": None
                }
                
                if self.config:
                    status["grid_master"] = self.config.grid_master_ip
                    status["wapi_version"] = self.config.wapi_version
                    
                    if self.client:
                        try:
                            status["connected"] = self.client.test_connection()
                        except Exception as e:
                            status["connection_error"] = str(e)
                
                return json.dumps(status, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return self.tool_registry.get_all_tools()
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                # Ensure we have a valid client
                await self._ensure_client()
                
                # Execute the tool
                result = await self.tool_registry.execute_tool(name, arguments, self.client)
                
                return [types.TextContent(type="text", text=result)]
                
            except InfoBloxAPIError as e:
                error_msg = f"InfoBlox API Error: {str(e)}"
                if e.status_code:
                    error_msg += f" (HTTP {e.status_code})"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
            
            except Exception as e:
                error_msg = f"Tool execution error: {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
    
    async def _ensure_client(self):
        """Ensure InfoBlox client is initialized."""
        if self.config is None:
            self.config = self.config_manager.get_config()
        
        if self.client is None:
            try:
                self.client = InfoBloxClient(self.config)
                logger.info("InfoBlox client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize InfoBlox client: {str(e)}")
                raise InfoBloxAPIError(f"Failed to connect to InfoBlox: {str(e)}")
    
    async def run(self):
        """Run the MCP server."""
        # Setup logging
        if self.config:
            logging.basicConfig(level=getattr(logging, self.config.log_level))
        else:
            logging.basicConfig(level=logging.INFO)
        
        logger.info("Starting InfoBlox MCP Server")
        
        try:
            # Initialize client on startup
            await self._ensure_client()
            
            # Run the server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="infoblox-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities=None
                        )
                    )
                )
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
        finally:
            if self.client:
                self.client.logout()
                logger.info("InfoBlox client disconnected")


def main():
    """Main entry point for the MCP server."""
    import sys
    import json
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reset-config":
            config_manager = ConfigManager()
            if config_manager.reset_config():
                print("Configuration reset successfully")
            else:
                print("Failed to reset configuration")
            return
        elif sys.argv[1] == "--test-connection":
            config_manager = ConfigManager()
            config = config_manager.load_config()
            if config is None:
                print("No configuration found. Run without arguments to configure.")
                return
            
            try:
                with InfoBloxClient(config) as client:
                    if client.test_connection():
                        print("Connection test successful")
                    else:
                        print("Connection test failed")
            except Exception as e:
                print(f"Connection test failed: {str(e)}")
            return
        elif sys.argv[1] == "--help":
            print("InfoBlox MCP Server")
            print("Usage:")
            print("  infoblox-mcp-server              Run the MCP server")
            print("  infoblox-mcp-server --reset-config    Reset configuration")
            print("  infoblox-mcp-server --test-connection Test InfoBlox connection")
            print("  infoblox-mcp-server --help            Show this help")
            return
    
    # Run the server
    server = InfoBloxMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

