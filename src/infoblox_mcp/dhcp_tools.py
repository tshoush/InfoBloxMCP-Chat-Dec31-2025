"""Extended tool implementations for InfoBlox MCP Server - DHCP Tools."""

import json
import logging
from typing import Any, Dict, List, Optional
from .client import InfoBloxClient, InfoBloxAPIError


logger = logging.getLogger(__name__)


class DHCPTools:
    """DHCP management tools for InfoBlox."""
    
    @staticmethod
    def register_tools(registry):
        """Register all DHCP tools."""
        
        # Network Management
        registry.register_tool(
            "infoblox_dhcp_delete_network",
            "Delete a DHCP network",
            {
                "type": "object",
                "properties": {
                    "network_ref": {
                        "type": "string",
                        "description": "Network reference or CIDR notation"
                    }
                },
                "required": ["network_ref"]
            },
            DHCPTools._delete_network
        )
        
        registry.register_tool(
            "infoblox_dhcp_get_network_details",
            "Get detailed information about a DHCP network",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network in CIDR format"
                    }
                },
                "required": ["network"]
            },
            DHCPTools._get_network_details
        )
        
        # IP Address Management
        registry.register_tool(
            "infoblox_dhcp_create_fixed_address",
            "Create a fixed address reservation",
            {
                "type": "object",
                "properties": {
                    "ipv4addr": {
                        "type": "string",
                        "description": "IPv4 address to reserve"
                    },
                    "mac": {
                        "type": "string",
                        "description": "MAC address (optional)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the reservation (optional)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the reservation (optional)"
                    }
                },
                "required": ["ipv4addr"]
            },
            DHCPTools._create_fixed_address
        )
        
        registry.register_tool(
            "infoblox_dhcp_list_fixed_addresses",
            "List all fixed address reservations",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Filter by network (optional)"
                    },
                    "mac": {
                        "type": "string",
                        "description": "Filter by MAC address (optional)"
                    }
                }
            },
            DHCPTools._list_fixed_addresses
        )
        
        registry.register_tool(
            "infoblox_dhcp_delete_fixed_address",
            "Delete a fixed address reservation",
            {
                "type": "object",
                "properties": {
                    "fixed_address_ref": {
                        "type": "string",
                        "description": "Fixed address reference or IP address"
                    }
                },
                "required": ["fixed_address_ref"]
            },
            DHCPTools._delete_fixed_address
        )
        
        # DHCP Ranges
        registry.register_tool(
            "infoblox_dhcp_create_range",
            "Create a DHCP range within a network",
            {
                "type": "object",
                "properties": {
                    "start_addr": {
                        "type": "string",
                        "description": "Start IP address of the range"
                    },
                    "end_addr": {
                        "type": "string",
                        "description": "End IP address of the range"
                    },
                    "network": {
                        "type": "string",
                        "description": "Parent network in CIDR format (optional)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the range (optional)"
                    }
                },
                "required": ["start_addr", "end_addr"]
            },
            DHCPTools._create_range
        )
        
        registry.register_tool(
            "infoblox_dhcp_list_ranges",
            "List all DHCP ranges",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Filter by network (optional)"
                    }
                }
            },
            DHCPTools._list_ranges
        )
        
        # DHCP Options
        registry.register_tool(
            "infoblox_dhcp_list_options",
            "List DHCP option definitions",
            {
                "type": "object",
                "properties": {
                    "space": {
                        "type": "string",
                        "description": "Option space (optional, defaults to 'DHCP')"
                    }
                }
            },
            DHCPTools._list_options
        )
        
        registry.register_tool(
            "infoblox_dhcp_create_option",
            "Create a custom DHCP option definition",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Option name"
                    },
                    "code": {
                        "type": "integer",
                        "description": "Option code",
                        "minimum": 1,
                        "maximum": 254
                    },
                    "type": {
                        "type": "string",
                        "enum": ["TEXT", "IP", "UINT8", "UINT16", "UINT32", "BOOLEAN"],
                        "description": "Option data type"
                    },
                    "space": {
                        "type": "string",
                        "description": "Option space (optional, defaults to 'DHCP')"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the option (optional)"
                    }
                },
                "required": ["name", "code", "type"]
            },
            DHCPTools._create_option
        )
        
        registry.register_tool(
            "infoblox_dhcp_assign_option_to_network",
            "Assign a DHCP option to a network",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network in CIDR format"
                    },
                    "option_name": {
                        "type": "string",
                        "description": "DHCP option name"
                    },
                    "value": {
                        "type": "string",
                        "description": "Option value"
                    }
                },
                "required": ["network", "option_name", "value"]
            },
            DHCPTools._assign_option_to_network
        )
        
        # Lease Management
        registry.register_tool(
            "infoblox_dhcp_list_leases",
            "List active DHCP leases",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Filter by network (optional)"
                    },
                    "ip_address": {
                        "type": "string",
                        "description": "Filter by IP address (optional)"
                    },
                    "mac_address": {
                        "type": "string",
                        "description": "Filter by MAC address (optional)"
                    },
                    "client_hostname": {
                        "type": "string",
                        "description": "Filter by client hostname (optional)"
                    }
                }
            },
            DHCPTools._list_leases
        )
        
        registry.register_tool(
            "infoblox_dhcp_clear_lease",
            "Clear a specific DHCP lease",
            {
                "type": "object",
                "properties": {
                    "lease_ref": {
                        "type": "string",
                        "description": "Lease reference or IP address"
                    }
                },
                "required": ["lease_ref"]
            },
            DHCPTools._clear_lease
        )
        
        registry.register_tool(
            "infoblox_dhcp_get_lease_history",
            "Get DHCP lease history for an IP address",
            {
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "description": "IP address to get history for"
                    }
                },
                "required": ["ip_address"]
            },
            DHCPTools._get_lease_history
        )
        
        # Network Containers
        registry.register_tool(
            "infoblox_dhcp_list_network_containers",
            "List network containers",
            {
                "type": "object",
                "properties": {
                    "network_view": {
                        "type": "string",
                        "description": "Network view name (optional)"
                    }
                }
            },
            DHCPTools._list_network_containers
        )
        
        registry.register_tool(
            "infoblox_dhcp_create_network_container",
            "Create a network container",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network container in CIDR format"
                    },
                    "network_view": {
                        "type": "string",
                        "description": "Network view name (optional, defaults to 'default')"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the container (optional)"
                    }
                },
                "required": ["network"]
            },
            DHCPTools._create_network_container
        )
    
    # Implementation methods
    
    @staticmethod
    async def _delete_network(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Delete DHCP network."""
        try:
            network_ref = args["network_ref"]
            
            # If it's not a reference, try to find the network
            if not network_ref.startswith("network/"):
                networks = client.search_objects("network", {"network": network_ref})
                if not networks:
                    raise InfoBloxAPIError(f"Network {network_ref} not found")
                network_ref = networks[0]["_ref"]
            
            client.delete_object(network_ref)
            
            result = {
                "success": True,
                "message": f"Network {args['network_ref']} deleted successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error deleting DHCP network: {str(e)}")
            raise InfoBloxAPIError(f"Failed to delete DHCP network: {str(e)}")
    
    @staticmethod
    async def _get_network_details(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get network details."""
        try:
            networks = client.search_objects("network", {"network": args["network"]})
            if not networks:
                raise InfoBloxAPIError(f"Network {args['network']} not found")
            
            network_ref = networks[0]["_ref"]
            network_details = client.get_object_by_ref(network_ref)
            
            return json.dumps(network_details, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting network details: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get network details: {str(e)}")
    
    @staticmethod
    async def _create_fixed_address(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create fixed address reservation."""
        try:
            fixed_addr_data = {
                "ipv4addr": args["ipv4addr"]
            }
            
            if "mac" in args:
                fixed_addr_data["mac"] = args["mac"]
            if "name" in args:
                fixed_addr_data["name"] = args["name"]
            if "comment" in args:
                fixed_addr_data["comment"] = args["comment"]
            
            fixed_addr_ref = client.create_object("fixedaddress", fixed_addr_data)
            
            result = {
                "success": True,
                "fixed_address_reference": fixed_addr_ref,
                "ipv4addr": args["ipv4addr"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating fixed address: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create fixed address: {str(e)}")
    
    @staticmethod
    async def _list_fixed_addresses(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List fixed addresses."""
        try:
            params = {}
            if "network" in args:
                params["network"] = args["network"]
            if "mac" in args:
                params["mac"] = args["mac"]
            
            fixed_addresses = client.search_objects("fixedaddress", params)
            
            result = {
                "fixed_addresses": fixed_addresses,
                "count": len(fixed_addresses)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing fixed addresses: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list fixed addresses: {str(e)}")
    
    @staticmethod
    async def _delete_fixed_address(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Delete fixed address."""
        try:
            fixed_addr_ref = args["fixed_address_ref"]
            
            # If it's not a reference, try to find by IP
            if not fixed_addr_ref.startswith("fixedaddress/"):
                fixed_addrs = client.search_objects("fixedaddress", {"ipv4addr": fixed_addr_ref})
                if not fixed_addrs:
                    raise InfoBloxAPIError(f"Fixed address {fixed_addr_ref} not found")
                fixed_addr_ref = fixed_addrs[0]["_ref"]
            
            client.delete_object(fixed_addr_ref)
            
            result = {
                "success": True,
                "message": f"Fixed address {args['fixed_address_ref']} deleted successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error deleting fixed address: {str(e)}")
            raise InfoBloxAPIError(f"Failed to delete fixed address: {str(e)}")
    
    @staticmethod
    async def _create_range(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DHCP range."""
        try:
            range_data = {
                "start_addr": args["start_addr"],
                "end_addr": args["end_addr"]
            }
            
            if "network" in args:
                range_data["network"] = args["network"]
            if "comment" in args:
                range_data["comment"] = args["comment"]
            
            range_ref = client.create_object("range", range_data)
            
            result = {
                "success": True,
                "range_reference": range_ref,
                "start_addr": args["start_addr"],
                "end_addr": args["end_addr"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DHCP range: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DHCP range: {str(e)}")
    
    @staticmethod
    async def _list_ranges(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DHCP ranges."""
        try:
            params = {}
            if "network" in args:
                params["network"] = args["network"]
            
            ranges = client.search_objects("range", params)
            
            result = {
                "ranges": ranges,
                "count": len(ranges)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DHCP ranges: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DHCP ranges: {str(e)}")
    
    @staticmethod
    async def _list_options(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DHCP options."""
        try:
            params = {}
            if "space" in args:
                params["space"] = args["space"]
            
            options = client.search_objects("dhcpoptiondefinition", params)
            
            result = {
                "options": options,
                "count": len(options)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DHCP options: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DHCP options: {str(e)}")
    
    @staticmethod
    async def _create_option(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DHCP option."""
        try:
            option_data = {
                "name": args["name"],
                "code": args["code"],
                "type": args["type"]
            }
            
            if "space" in args:
                option_data["space"] = args["space"]
            if "comment" in args:
                option_data["comment"] = args["comment"]
            
            option_ref = client.create_object("dhcpoptiondefinition", option_data)
            
            result = {
                "success": True,
                "option_reference": option_ref,
                "name": args["name"],
                "code": args["code"],
                "type": args["type"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DHCP option: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DHCP option: {str(e)}")
    
    @staticmethod
    async def _assign_option_to_network(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Assign DHCP option to network."""
        try:
            # Find the network
            networks = client.search_objects("network", {"network": args["network"]})
            if not networks:
                raise InfoBloxAPIError(f"Network {args['network']} not found")
            
            network_ref = networks[0]["_ref"]
            
            # Update network with DHCP option
            option_data = {
                "options": [
                    {
                        "name": args["option_name"],
                        "value": args["value"]
                    }
                ]
            }
            
            result = client.update_object(network_ref, option_data)
            
            return json.dumps({
                "success": True,
                "network": args["network"],
                "option_name": args["option_name"],
                "value": args["value"],
                "result": result
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error assigning DHCP option to network: {str(e)}")
            raise InfoBloxAPIError(f"Failed to assign DHCP option to network: {str(e)}")
    
    @staticmethod
    async def _list_leases(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DHCP leases."""
        try:
            params = {}
            if "network" in args:
                params["network"] = args["network"]
            if "ip_address" in args:
                params["ip_address"] = args["ip_address"]
            if "mac_address" in args:
                params["mac_address"] = args["mac_address"]
            if "client_hostname" in args:
                params["client_hostname"] = args["client_hostname"]
            
            leases = client.search_objects("lease", params)
            
            result = {
                "leases": leases,
                "count": len(leases)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DHCP leases: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DHCP leases: {str(e)}")
    
    @staticmethod
    async def _clear_lease(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Clear DHCP lease."""
        try:
            lease_ref = args["lease_ref"]
            
            # If it's not a reference, try to find by IP
            if not lease_ref.startswith("lease/"):
                leases = client.search_objects("lease", {"ip_address": lease_ref})
                if not leases:
                    raise InfoBloxAPIError(f"Lease for {lease_ref} not found")
                lease_ref = leases[0]["_ref"]
            
            client.delete_object(lease_ref)
            
            result = {
                "success": True,
                "message": f"Lease {args['lease_ref']} cleared successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error clearing DHCP lease: {str(e)}")
            raise InfoBloxAPIError(f"Failed to clear DHCP lease: {str(e)}")
    
    @staticmethod
    async def _get_lease_history(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get lease history."""
        try:
            # This would typically require a specific API call or search
            # For now, we'll search for historical lease data
            params = {
                "ip_address": args["ip_address"],
                "_return_fields": "ip_address,mac_address,client_hostname,starts,ends,binding_state"
            }
            
            lease_history = client.search_objects("lease", params)
            
            result = {
                "ip_address": args["ip_address"],
                "lease_history": lease_history,
                "count": len(lease_history)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting lease history: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get lease history: {str(e)}")
    
    @staticmethod
    async def _list_network_containers(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List network containers."""
        try:
            params = {}
            if "network_view" in args:
                params["network_view"] = args["network_view"]
            
            containers = client.search_objects("networkcontainer", params)
            
            result = {
                "network_containers": containers,
                "count": len(containers)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing network containers: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list network containers: {str(e)}")
    
    @staticmethod
    async def _create_network_container(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create network container."""
        try:
            container_data = {
                "network": args["network"]
            }
            
            if "network_view" in args:
                container_data["network_view"] = args["network_view"]
            if "comment" in args:
                container_data["comment"] = args["comment"]
            
            container_ref = client.create_object("networkcontainer", container_data)
            
            result = {
                "success": True,
                "container_reference": container_ref,
                "network": args["network"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating network container: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create network container: {str(e)}")

