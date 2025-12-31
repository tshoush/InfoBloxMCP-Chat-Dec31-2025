"""Tool registry and implementations for InfoBlox MCP Server."""

import json
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
from mcp.types import Tool
from .client import InfoBloxClient, InfoBloxAPIError
from .dns_tools import DNSTools
from .dhcp_tools import DHCPTools
from .additional_tools import IPAMTools, GridTools, BulkTools, AnalysisTools
from .splunk_tools import SplunkTools


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for InfoBlox MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_all_tools()
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[[Dict[str, Any], InfoBloxClient], Awaitable[str]]
    ):
        """Register a tool."""
        self.tools[name] = {
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools as MCP Tool objects."""
        tools = []
        for name, tool_info in self.tools.items():
            tools.append(Tool(
                name=name,
                description=tool_info["description"],
                inputSchema=tool_info["parameters"]
            ))
        return tools
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any], client: InfoBloxClient) -> str:
        """Execute a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        handler = self.tools[name]["handler"]
        return await handler(arguments, client)
    
    def _register_all_tools(self):
        """Register all InfoBlox tools."""
        # Register basic DNS and DHCP tools first
        self._register_basic_dns_tools()
        self._register_basic_dhcp_tools()
        self._register_basic_ipam_tools()
        self._register_basic_grid_tools()
        
        # Register extended tools from separate modules
        DNSTools.register_tools(self)
        DHCPTools.register_tools(self)
        IPAMTools.register_tools(self)
        GridTools.register_tools(self)
        BulkTools.register_tools(self)
        AnalysisTools.register_tools(self)
        SplunkTools.register_tools(self)
    
    def _register_basic_dns_tools(self):
        """Register basic DNS management tools."""
        
        # List DNS zones
        self.register_tool(
            "infoblox_dns_list_zones",
            "List all DNS zones in the InfoBlox system",
            {
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional, defaults to 'default')"
                    },
                    "zone_format": {
                        "type": "string",
                        "enum": ["FORWARD", "REVERSE", "IPV6"],
                        "description": "Zone format filter (optional)"
                    }
                }
            },
            self._dns_list_zones
        )
        
        # Create DNS zone
        self.register_tool(
            "infoblox_dns_create_zone",
            "Create a new DNS zone",
            {
                "type": "object",
                "properties": {
                    "fqdn": {
                        "type": "string",
                        "description": "Fully qualified domain name for the zone"
                    },
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional, defaults to 'default')"
                    },
                    "zone_format": {
                        "type": "string",
                        "enum": ["FORWARD", "REVERSE", "IPV6"],
                        "description": "Zone format (optional, defaults to 'FORWARD')"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the zone (optional)"
                    }
                },
                "required": ["fqdn"]
            },
            self._dns_create_zone
        )
        
        # Create A record
        self.register_tool(
            "infoblox_dns_create_record_a",
            "Create a DNS A record",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Record name (hostname)"
                    },
                    "ipv4addr": {
                        "type": "string",
                        "description": "IPv4 address"
                    },
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional, defaults to 'default')"
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "Time to live in seconds (optional)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the record (optional)"
                    }
                },
                "required": ["name", "ipv4addr"]
            },
            self._dns_create_record_a
        )
        
        # Search DNS records
        self.register_tool(
            "infoblox_dns_search_records",
            "Search for DNS records",
            {
                "type": "object",
                "properties": {
                    "record_type": {
                        "type": "string",
                        "enum": ["A", "AAAA", "CNAME", "MX", "PTR", "SRV", "TXT"],
                        "description": "Type of DNS record to search for"
                    },
                    "name": {
                        "type": "string",
                        "description": "Record name to search for (supports wildcards)"
                    },
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to search for (for A/AAAA records)"
                    },
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional, defaults to 'default')"
                    },
                    "zone": {
                        "type": "string",
                        "description": "Zone to search within (optional)"
                    }
                },
                "required": ["record_type"]
            },
            self._dns_search_records
        )
    
    def _register_basic_dhcp_tools(self):
        """Register basic DHCP management tools."""
        
        # List DHCP networks
        self.register_tool(
            "infoblox_dhcp_list_networks",
            "List all DHCP networks",
            {
                "type": "object",
                "properties": {
                    "network_view": {
                        "type": "string",
                        "description": "Network view name (optional, defaults to 'default')"
                    },
                    "network_container": {
                        "type": "string",
                        "description": "Filter by network container (optional)"
                    }
                }
            },
            self._dhcp_list_networks
        )
        
        # Create DHCP network
        self.register_tool(
            "infoblox_dhcp_create_network",
            "Create a new DHCP network",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network address in CIDR format (e.g., '192.168.1.0/24')"
                    },
                    "network_view": {
                        "type": "string",
                        "description": "Network view name (optional, defaults to 'default')"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the network (optional)"
                    }
                },
                "required": ["network"]
            },
            self._dhcp_create_network
        )
        
        # Get next available IP
        self.register_tool(
            "infoblox_dhcp_get_next_available_ip",
            "Get the next available IP address in a network",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network address in CIDR format"
                    },
                    "num_ips": {
                        "type": "integer",
                        "description": "Number of IP addresses to retrieve (default: 1)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["network"]
            },
            self._dhcp_get_next_available_ip
        )
    
    def _register_basic_ipam_tools(self):
        """Register basic IPAM tools."""
        
        # Get network utilization
        self.register_tool(
            "infoblox_ipam_get_network_utilization",
            "Get network utilization statistics",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network address in CIDR format"
                    }
                },
                "required": ["network"]
            },
            self._ipam_get_network_utilization
        )
    
    def _register_basic_grid_tools(self):
        """Register basic Grid management tools."""
        
        # List grid members
        self.register_tool(
            "infoblox_grid_list_members",
            "List all grid members",
            {
                "type": "object",
                "properties": {}
            },
            self._grid_list_members
        )
        
        # Get grid status
        self.register_tool(
            "infoblox_grid_get_status",
            "Get grid system status",
            {
                "type": "object",
                "properties": {}
            },
            self._grid_get_status
        )
    
    # Basic tool implementation methods
    
    async def _dns_list_zones(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DNS zones."""
        try:
            params = {}
            if "view" in args:
                params["view"] = args["view"]
            if "zone_format" in args:
                params["zone_format"] = args["zone_format"]
            
            zones = client.search_objects("zone_auth", params)
            
            result = {
                "zones": zones,
                "count": len(zones)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DNS zones: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DNS zones: {str(e)}")
    
    async def _dns_create_zone(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS zone."""
        try:
            zone_data = {
                "fqdn": args["fqdn"]
            }
            
            if "view" in args:
                zone_data["view"] = args["view"]
            if "zone_format" in args:
                zone_data["zone_format"] = args["zone_format"]
            if "comment" in args:
                zone_data["comment"] = args["comment"]
            
            zone_ref = client.create_object("zone_auth", zone_data)
            
            result = {
                "success": True,
                "zone_reference": zone_ref,
                "fqdn": args["fqdn"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS zone: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS zone: {str(e)}")
    
    async def _dns_create_record_a(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS A record."""
        try:
            record_data = {
                "name": args["name"],
                "ipv4addr": args["ipv4addr"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:a", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "ipv4addr": args["ipv4addr"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS A record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS A record: {str(e)}")
    
    async def _dns_search_records(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Search DNS records."""
        try:
            record_type_map = {
                "A": "record:a",
                "AAAA": "record:aaaa",
                "CNAME": "record:cname",
                "MX": "record:mx",
                "PTR": "record:ptr",
                "SRV": "record:srv",
                "TXT": "record:txt"
            }
            
            object_type = record_type_map.get(args["record_type"])
            if not object_type:
                raise ValueError(f"Unsupported record type: {args['record_type']}")
            
            params = {}
            if "name" in args:
                params["name"] = args["name"]
            if "ip_address" in args and args["record_type"] in ["A", "AAAA"]:
                if args["record_type"] == "A":
                    params["ipv4addr"] = args["ip_address"]
                else:
                    params["ipv6addr"] = args["ip_address"]
            if "view" in args:
                params["view"] = args["view"]
            if "zone" in args:
                params["zone"] = args["zone"]
            
            records = client.search_objects(object_type, params)
            
            result = {
                "records": records,
                "count": len(records),
                "record_type": args["record_type"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error searching DNS records: {str(e)}")
            raise InfoBloxAPIError(f"Failed to search DNS records: {str(e)}")
    
    async def _dhcp_list_networks(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DHCP networks."""
        try:
            params = {}
            if "network_view" in args:
                params["network_view"] = args["network_view"]
            if "network_container" in args:
                params["network_container"] = args["network_container"]
            
            networks = client.search_objects("network", params)
            
            result = {
                "networks": networks,
                "count": len(networks)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DHCP networks: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DHCP networks: {str(e)}")
    
    async def _dhcp_create_network(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DHCP network."""
        try:
            network_data = {
                "network": args["network"]
            }
            
            if "network_view" in args:
                network_data["network_view"] = args["network_view"]
            if "comment" in args:
                network_data["comment"] = args["comment"]
            
            network_ref = client.create_object("network", network_data)
            
            result = {
                "success": True,
                "network_reference": network_ref,
                "network": args["network"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DHCP network: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DHCP network: {str(e)}")
    
    async def _dhcp_get_next_available_ip(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get next available IP."""
        try:
            num_ips = args.get("num_ips", 1)
            ips = client.get_next_available_ip(args["network"], num_ips)
            
            result = {
                "network": args["network"],
                "available_ips": ips,
                "count": len(ips)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting next available IP: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get next available IP: {str(e)}")
    
    async def _ipam_get_network_utilization(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get network utilization."""
        try:
            # First find the network object
            networks = client.search_objects("network", {"network": args["network"]})
            if not networks:
                raise InfoBloxAPIError(f"Network {args['network']} not found")
            
            network_ref = networks[0]["_ref"]
            utilization = client.get_network_utilization(network_ref)
            
            result = {
                "network": args["network"],
                "utilization": utilization
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting network utilization: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get network utilization: {str(e)}")
    
    async def _grid_list_members(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List grid members."""
        try:
            members = client.search_objects("member")
            
            result = {
                "members": members,
                "count": len(members)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing grid members: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list grid members: {str(e)}")
    
    async def _grid_get_status(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get grid status."""
        try:
            grid_info = client.search_objects("grid")
            
            result = {
                "grid_info": grid_info,
                "status": "operational" if grid_info else "unknown"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting grid status: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get grid status: {str(e)}")

