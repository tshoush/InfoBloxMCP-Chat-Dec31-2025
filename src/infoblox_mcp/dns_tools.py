"""Extended tool implementations for InfoBlox MCP Server - DNS Tools."""

import json
import logging
from typing import Any, Dict, List, Optional
from .client import InfoBloxClient, InfoBloxAPIError


logger = logging.getLogger(__name__)


class DNSTools:
    """DNS management tools for InfoBlox."""
    
    @staticmethod
    def register_tools(registry):
        """Register all DNS tools."""
        
        # Zone Management Tools
        registry.register_tool(
            "infoblox_dns_delete_zone",
            "Delete a DNS zone",
            {
                "type": "object",
                "properties": {
                    "zone_ref": {
                        "type": "string",
                        "description": "Zone reference (from list_zones) or FQDN"
                    }
                },
                "required": ["zone_ref"]
            },
            DNSTools._delete_zone
        )
        
        registry.register_tool(
            "infoblox_dns_get_zone_details",
            "Get detailed information about a DNS zone",
            {
                "type": "object",
                "properties": {
                    "zone_ref": {
                        "type": "string",
                        "description": "Zone reference or FQDN"
                    }
                },
                "required": ["zone_ref"]
            },
            DNSTools._get_zone_details
        )
        
        # DNS Record Management - AAAA Records
        registry.register_tool(
            "infoblox_dns_create_record_aaaa",
            "Create a DNS AAAA record (IPv6)",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Record name (hostname)"
                    },
                    "ipv6addr": {
                        "type": "string",
                        "description": "IPv6 address"
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
                "required": ["name", "ipv6addr"]
            },
            DNSTools._create_record_aaaa
        )
        
        # CNAME Records
        registry.register_tool(
            "infoblox_dns_create_record_cname",
            "Create a DNS CNAME record",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Record name (alias)"
                    },
                    "canonical": {
                        "type": "string",
                        "description": "Canonical name (target)"
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
                "required": ["name", "canonical"]
            },
            DNSTools._create_record_cname
        )
        
        # MX Records
        registry.register_tool(
            "infoblox_dns_create_record_mx",
            "Create a DNS MX record",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Domain name"
                    },
                    "mail_exchanger": {
                        "type": "string",
                        "description": "Mail exchanger hostname"
                    },
                    "preference": {
                        "type": "integer",
                        "description": "MX preference value",
                        "minimum": 0,
                        "maximum": 65535
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
                "required": ["name", "mail_exchanger", "preference"]
            },
            DNSTools._create_record_mx
        )
        
        # PTR Records
        registry.register_tool(
            "infoblox_dns_create_record_ptr",
            "Create a DNS PTR record (reverse lookup)",
            {
                "type": "object",
                "properties": {
                    "ipv4addr": {
                        "type": "string",
                        "description": "IPv4 address for reverse lookup"
                    },
                    "ptrdname": {
                        "type": "string",
                        "description": "Domain name for the PTR record"
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
                "required": ["ipv4addr", "ptrdname"]
            },
            DNSTools._create_record_ptr
        )
        
        # SRV Records
        registry.register_tool(
            "infoblox_dns_create_record_srv",
            "Create a DNS SRV record",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Service name (e.g., _sip._tcp.example.com)"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target hostname"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port number",
                        "minimum": 0,
                        "maximum": 65535
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority value",
                        "minimum": 0,
                        "maximum": 65535
                    },
                    "weight": {
                        "type": "integer",
                        "description": "Weight value",
                        "minimum": 0,
                        "maximum": 65535
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
                "required": ["name", "target", "port", "priority", "weight"]
            },
            DNSTools._create_record_srv
        )
        
        # TXT Records
        registry.register_tool(
            "infoblox_dns_create_record_txt",
            "Create a DNS TXT record",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Record name"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text content"
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
                "required": ["name", "text"]
            },
            DNSTools._create_record_txt
        )
        
        # Record Management
        registry.register_tool(
            "infoblox_dns_update_record",
            "Update an existing DNS record",
            {
                "type": "object",
                "properties": {
                    "record_ref": {
                        "type": "string",
                        "description": "Record reference (from search results)"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Fields to update (varies by record type)",
                        "additionalProperties": True
                    }
                },
                "required": ["record_ref", "updates"]
            },
            DNSTools._update_record
        )
        
        registry.register_tool(
            "infoblox_dns_delete_record",
            "Delete a DNS record",
            {
                "type": "object",
                "properties": {
                    "record_ref": {
                        "type": "string",
                        "description": "Record reference (from search results)"
                    }
                },
                "required": ["record_ref"]
            },
            DNSTools._delete_record
        )
        
        # DNS Views
        registry.register_tool(
            "infoblox_dns_list_views",
            "List all DNS views",
            {
                "type": "object",
                "properties": {}
            },
            DNSTools._list_views
        )
        
        registry.register_tool(
            "infoblox_dns_create_view",
            "Create a new DNS view",
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "View name"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the view (optional)"
                    }
                },
                "required": ["name"]
            },
            DNSTools._create_view
        )
        
        # Response Policy Zones (RPZ)
        registry.register_tool(
            "infoblox_dns_list_rpz_zones",
            "List Response Policy Zones",
            {
                "type": "object",
                "properties": {
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional)"
                    }
                }
            },
            DNSTools._list_rpz_zones
        )
        
        registry.register_tool(
            "infoblox_dns_create_rpz_zone",
            "Create a Response Policy Zone",
            {
                "type": "object",
                "properties": {
                    "fqdn": {
                        "type": "string",
                        "description": "RPZ zone FQDN"
                    },
                    "view": {
                        "type": "string",
                        "description": "DNS view name (optional, defaults to 'default')"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the RPZ zone (optional)"
                    }
                },
                "required": ["fqdn"]
            },
            DNSTools._create_rpz_zone
        )
    
    # Implementation methods
    
    @staticmethod
    async def _delete_zone(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Delete DNS zone."""
        try:
            zone_ref = args["zone_ref"]
            
            # If it's not a reference, try to find the zone
            if not zone_ref.startswith("zone_auth/"):
                zones = client.search_objects("zone_auth", {"fqdn": zone_ref})
                if not zones:
                    raise InfoBloxAPIError(f"Zone {zone_ref} not found")
                zone_ref = zones[0]["_ref"]
            
            client.delete_object(zone_ref)
            
            result = {
                "success": True,
                "message": f"Zone {args['zone_ref']} deleted successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error deleting DNS zone: {str(e)}")
            raise InfoBloxAPIError(f"Failed to delete DNS zone: {str(e)}")
    
    @staticmethod
    async def _get_zone_details(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get zone details."""
        try:
            zone_ref = args["zone_ref"]
            
            # If it's not a reference, try to find the zone
            if not zone_ref.startswith("zone_auth/"):
                zones = client.search_objects("zone_auth", {"fqdn": zone_ref})
                if not zones:
                    raise InfoBloxAPIError(f"Zone {zone_ref} not found")
                zone_ref = zones[0]["_ref"]
            
            zone_details = client.get_object_by_ref(zone_ref)
            
            return json.dumps(zone_details, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting zone details: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get zone details: {str(e)}")
    
    @staticmethod
    async def _create_record_aaaa(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS AAAA record."""
        try:
            record_data = {
                "name": args["name"],
                "ipv6addr": args["ipv6addr"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:aaaa", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "ipv6addr": args["ipv6addr"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS AAAA record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS AAAA record: {str(e)}")
    
    @staticmethod
    async def _create_record_cname(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS CNAME record."""
        try:
            record_data = {
                "name": args["name"],
                "canonical": args["canonical"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:cname", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "canonical": args["canonical"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS CNAME record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS CNAME record: {str(e)}")
    
    @staticmethod
    async def _create_record_mx(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS MX record."""
        try:
            record_data = {
                "name": args["name"],
                "mail_exchanger": args["mail_exchanger"],
                "preference": args["preference"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:mx", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "mail_exchanger": args["mail_exchanger"],
                "preference": args["preference"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS MX record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS MX record: {str(e)}")
    
    @staticmethod
    async def _create_record_ptr(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS PTR record."""
        try:
            record_data = {
                "ipv4addr": args["ipv4addr"],
                "ptrdname": args["ptrdname"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:ptr", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "ipv4addr": args["ipv4addr"],
                "ptrdname": args["ptrdname"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS PTR record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS PTR record: {str(e)}")
    
    @staticmethod
    async def _create_record_srv(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS SRV record."""
        try:
            record_data = {
                "name": args["name"],
                "target": args["target"],
                "port": args["port"],
                "priority": args["priority"],
                "weight": args["weight"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:srv", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "target": args["target"],
                "port": args["port"],
                "priority": args["priority"],
                "weight": args["weight"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS SRV record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS SRV record: {str(e)}")
    
    @staticmethod
    async def _create_record_txt(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS TXT record."""
        try:
            record_data = {
                "name": args["name"],
                "text": args["text"]
            }
            
            if "view" in args:
                record_data["view"] = args["view"]
            if "ttl" in args:
                record_data["ttl"] = args["ttl"]
            if "comment" in args:
                record_data["comment"] = args["comment"]
            
            record_ref = client.create_object("record:txt", record_data)
            
            result = {
                "success": True,
                "record_reference": record_ref,
                "name": args["name"],
                "text": args["text"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS TXT record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS TXT record: {str(e)}")
    
    @staticmethod
    async def _update_record(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Update DNS record."""
        try:
            record_ref = args["record_ref"]
            updates = args["updates"]
            
            result = client.update_object(record_ref, updates)
            
            return json.dumps({
                "success": True,
                "record_reference": record_ref,
                "updates": updates,
                "result": result
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error updating DNS record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to update DNS record: {str(e)}")
    
    @staticmethod
    async def _delete_record(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Delete DNS record."""
        try:
            record_ref = args["record_ref"]
            
            client.delete_object(record_ref)
            
            result = {
                "success": True,
                "message": f"Record {record_ref} deleted successfully"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error deleting DNS record: {str(e)}")
            raise InfoBloxAPIError(f"Failed to delete DNS record: {str(e)}")
    
    @staticmethod
    async def _list_views(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List DNS views."""
        try:
            views = client.search_objects("view")
            
            result = {
                "views": views,
                "count": len(views)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing DNS views: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list DNS views: {str(e)}")
    
    @staticmethod
    async def _create_view(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create DNS view."""
        try:
            view_data = {
                "name": args["name"]
            }
            
            if "comment" in args:
                view_data["comment"] = args["comment"]
            
            view_ref = client.create_object("view", view_data)
            
            result = {
                "success": True,
                "view_reference": view_ref,
                "name": args["name"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating DNS view: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create DNS view: {str(e)}")
    
    @staticmethod
    async def _list_rpz_zones(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List RPZ zones."""
        try:
            params = {}
            if "view" in args:
                params["view"] = args["view"]
            
            rpz_zones = client.search_objects("zone_rp", params)
            
            result = {
                "rpz_zones": rpz_zones,
                "count": len(rpz_zones)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing RPZ zones: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list RPZ zones: {str(e)}")
    
    @staticmethod
    async def _create_rpz_zone(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Create RPZ zone."""
        try:
            rpz_data = {
                "fqdn": args["fqdn"]
            }
            
            if "view" in args:
                rpz_data["view"] = args["view"]
            if "comment" in args:
                rpz_data["comment"] = args["comment"]
            
            rpz_ref = client.create_object("zone_rp", rpz_data)
            
            result = {
                "success": True,
                "rpz_reference": rpz_ref,
                "fqdn": args["fqdn"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating RPZ zone: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create RPZ zone: {str(e)}")

