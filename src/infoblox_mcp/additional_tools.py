"""Extended tool implementations for InfoBlox MCP Server - Additional Tools."""

import json
import logging
from typing import Any, Dict, List, Optional
from .client import InfoBloxClient, InfoBloxAPIError
import csv
import ast


logger = logging.getLogger(__name__)


class IPAMTools:
    """IPAM (IP Address Management) tools for InfoBlox."""
    
    @staticmethod
    def register_tools(registry):
        """Register all IPAM tools."""
        
        # Network Discovery
        registry.register_tool(
            "infoblox_ipam_discover_networks",
            "Discover networks in the infrastructure",
            {
                "type": "object",
                "properties": {
                    "network_view": {
                        "type": "string",
                        "description": "Network view to discover in (optional)"
                    },
                    "discovery_member": {
                        "type": "string",
                        "description": "Grid member to perform discovery (optional)"
                    }
                }
            },
            IPAMTools._discover_networks
        )
        
        registry.register_tool(
            "infoblox_ipam_scan_network",
            "Scan a specific network for active hosts",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network to scan in CIDR format"
                    },
                    "scan_type": {
                        "type": "string",
                        "enum": ["PING", "TCP_SCAN", "SNMP"],
                        "description": "Type of scan to perform (optional, defaults to PING)"
                    }
                },
                "required": ["network"]
            },
            IPAMTools._scan_network
        )
        
        # IP Address Planning
        registry.register_tool(
            "infoblox_ipam_find_next_available_network",
            "Find the next available subnet within a container",
            {
                "type": "object",
                "properties": {
                    "container": {
                        "type": "string",
                        "description": "Network container in CIDR format"
                    },
                    "cidr": {
                        "type": "integer",
                        "description": "CIDR prefix length for the new subnet",
                        "minimum": 8,
                        "maximum": 30
                    },
                    "num_networks": {
                        "type": "integer",
                        "description": "Number of networks to find (default: 1)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["container", "cidr"]
            },
            IPAMTools._find_next_available_network
        )
        
        registry.register_tool(
            "infoblox_ipam_calculate_subnets",
            "Calculate subnet divisions for a network",
            {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Network to divide in CIDR format"
                    },
                    "subnet_size": {
                        "type": "integer",
                        "description": "Size of each subnet (CIDR prefix)",
                        "minimum": 8,
                        "maximum": 30
                    }
                },
                "required": ["network", "subnet_size"]
            },
            IPAMTools._calculate_subnets
        )
        
        # Utilization and Reporting
        registry.register_tool(
            "infoblox_ipam_get_utilization_summary",
            "Get utilization summary for all networks",
            {
                "type": "object",
                "properties": {
                    "network_view": {
                        "type": "string",
                        "description": "Network view to analyze (optional)"
                    },
                    "threshold": {
                        "type": "integer",
                        "description": "Utilization threshold percentage (optional)",
                        "minimum": 0,
                        "maximum": 100
                    }
                }
            },
            IPAMTools._get_utilization_summary
        )
    
    @staticmethod
    async def _discover_networks(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Discover networks."""
        try:
            # Start network discovery
            discovery_data = {}
            if "network_view" in args:
                discovery_data["network_view"] = args["network_view"]
            if "discovery_member" in args:
                discovery_data["discovery_member"] = args["discovery_member"]
            
            # This would typically trigger a discovery task
            discovery_ref = client.create_object("discoverytask", discovery_data)
            
            result = {
                "success": True,
                "discovery_reference": discovery_ref,
                "message": "Network discovery started"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error starting network discovery: {str(e)}")
            raise InfoBloxAPIError(f"Failed to start network discovery: {str(e)}")
    
    @staticmethod
    async def _scan_network(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Scan network for active hosts."""
        try:
            scan_data = {
                "network": args["network"],
                "scan_type": args.get("scan_type", "PING")
            }
            
            # This would typically use the discovery functionality
            scan_result = client.post("discovery", data=scan_data)
            
            result = {
                "network": args["network"],
                "scan_type": args.get("scan_type", "PING"),
                "scan_result": scan_result
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error scanning network: {str(e)}")
            raise InfoBloxAPIError(f"Failed to scan network: {str(e)}")
    
    @staticmethod
    async def _find_next_available_network(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Find next available network."""
        try:
            container = args["container"]
            cidr = args["cidr"]
            num_networks = args.get("num_networks", 1)
            
            # Use the next_available_network function
            params = {
                "_function": "next_available_network",
                "cidr": cidr,
                "num": num_networks
            }
            
            result = client.post(f"networkcontainer/{container}", params=params)
            
            return json.dumps({
                "container": container,
                "cidr": cidr,
                "available_networks": result,
                "count": len(result) if isinstance(result, list) else 1
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error finding next available network: {str(e)}")
            raise InfoBloxAPIError(f"Failed to find next available network: {str(e)}")
    
    @staticmethod
    async def _calculate_subnets(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Calculate subnet divisions."""
        try:
            import ipaddress
            
            network = ipaddress.ip_network(args["network"])
            subnet_size = args["subnet_size"]
            
            # Calculate how many subnets we can create
            subnets = list(network.subnets(new_prefix=subnet_size))
            
            result = {
                "original_network": str(network),
                "subnet_size": subnet_size,
                "total_subnets": len(subnets),
                "subnets": [str(subnet) for subnet in subnets[:100]]  # Limit to first 100
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error calculating subnets: {str(e)}")
            raise InfoBloxAPIError(f"Failed to calculate subnets: {str(e)}")
    
    @staticmethod
    async def _get_utilization_summary(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get utilization summary."""
        try:
            params = {}
            if "network_view" in args:
                params["network_view"] = args["network_view"]
            
            # Get all networks (limit to 500 for safety)
            if "_max_results" not in params:
                 params["_max_results"] = 500
            
            networks = client.search_objects("network", params)
            
            utilization_data = []
            threshold = args.get("threshold", 80)
            
            for network in networks:
                try:
                    network_ref = network["_ref"]
                    utilization = client.get_network_utilization(network_ref)
                    
                    if isinstance(utilization, dict):
                        util_percent = utilization.get("utilization", 0)
                        if util_percent >= threshold:
                            utilization_data.append({
                                "network": network.get("network", "Unknown"),
                                "utilization": utilization,
                                "above_threshold": True
                            })
                        else:
                            utilization_data.append({
                                "network": network.get("network", "Unknown"),
                                "utilization": utilization,
                                "above_threshold": False
                            })
                except Exception as e:
                    logger.warning(f"Could not get utilization for network {network.get('network', 'Unknown')}: {str(e)}")
            
            result = {
                "threshold": threshold,
                "total_networks": len(networks),
                "networks_analyzed": len(utilization_data),
                "networks_above_threshold": len([n for n in utilization_data if n["above_threshold"]]),
                "utilization_data": utilization_data
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting utilization summary: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get utilization summary: {str(e)}")


class GridTools:
    """Grid management tools for InfoBlox."""
    
    @staticmethod
    def register_tools(registry):
        """Register all Grid tools."""
        
        # Member Management
        registry.register_tool(
            "infoblox_grid_get_member_details",
            "Get detailed information about a grid member",
            {
                "type": "object",
                "properties": {
                    "member_name": {
                        "type": "string",
                        "description": "Grid member hostname or IP"
                    }
                },
                "required": ["member_name"]
            },
            GridTools._get_member_details
        )
        
        registry.register_tool(
            "infoblox_grid_restart_services",
            "Restart services on a grid member",
            {
                "type": "object",
                "properties": {
                    "member_name": {
                        "type": "string",
                        "description": "Grid member hostname or IP"
                    },
                    "service_option": {
                        "type": "string",
                        "enum": ["ALL", "DNS", "DHCP", "NTP"],
                        "description": "Service to restart (optional, defaults to ALL)"
                    }
                },
                "required": ["member_name"]
            },
            GridTools._restart_services
        )
        
        # Configuration Management
        registry.register_tool(
            "infoblox_grid_backup_database",
            "Create a database backup",
            {
                "type": "object",
                "properties": {
                    "backup_type": {
                        "type": "string",
                        "enum": ["DATABASE", "DHCP_LEASES"],
                        "description": "Type of backup (optional, defaults to DATABASE)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment for the backup (optional)"
                    }
                }
            },
            GridTools._backup_database
        )
        
        registry.register_tool(
            "infoblox_grid_list_backups",
            "List available database backups",
            {
                "type": "object",
                "properties": {}
            },
            GridTools._list_backups
        )
        
        # System Information
        registry.register_tool(
            "infoblox_grid_get_system_info",
            "Get grid system information",
            {
                "type": "object",
                "properties": {}
            },
            GridTools._get_system_info
        )
        
        registry.register_tool(
            "infoblox_grid_get_capacity_report",
            "Get grid capacity and performance report",
            {
                "type": "object",
                "properties": {
                    "member_name": {
                        "type": "string",
                        "description": "Specific member to report on (optional)"
                    }
                }
            },
            GridTools._get_capacity_report
        )
    
    @staticmethod
    async def _get_member_details(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get member details."""
        try:
            member_name = args["member_name"]
            
            # Search for the member
            members = client.search_objects("member", {"host_name": member_name})
            if not members:
                # Try searching by IP
                members = client.search_objects("member", {"ipv4_address": member_name})
            
            if not members:
                raise InfoBloxAPIError(f"Member {member_name} not found")
            
            member_ref = members[0]["_ref"]
            member_details = client.get_object_by_ref(member_ref)
            
            return json.dumps(member_details, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting member details: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get member details: {str(e)}")
    
    @staticmethod
    async def _restart_services(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Restart grid services."""
        try:
            member_name = args["member_name"]
            service_option = args.get("service_option", "ALL")
            
            # Find the member
            members = client.search_objects("member", {"host_name": member_name})
            if not members:
                raise InfoBloxAPIError(f"Member {member_name} not found")
            
            member_ref = members[0]["_ref"]
            
            # Restart services
            restart_data = {
                "service_option": service_option
            }
            
            result = client.post(f"{member_ref}?_function=restartservices", data=restart_data)
            
            return json.dumps({
                "success": True,
                "member": member_name,
                "service_option": service_option,
                "result": result
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error restarting services: {str(e)}")
            raise InfoBloxAPIError(f"Failed to restart services: {str(e)}")
    
    @staticmethod
    async def _backup_database(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Backup database."""
        try:
            backup_data = {
                "backup_type": args.get("backup_type", "DATABASE")
            }
            
            if "comment" in args:
                backup_data["comment"] = args["comment"]
            
            # Create backup
            backup_ref = client.create_object("dbsnapshot", backup_data)
            
            result = {
                "success": True,
                "backup_reference": backup_ref,
                "backup_type": backup_data["backup_type"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise InfoBloxAPIError(f"Failed to create backup: {str(e)}")
    
    @staticmethod
    async def _list_backups(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """List backups."""
        try:
            backups = client.search_objects("dbsnapshot")
            
            result = {
                "backups": backups,
                "count": len(backups)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            raise InfoBloxAPIError(f"Failed to list backups: {str(e)}")
    
    @staticmethod
    async def _get_system_info(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get system information."""
        try:
            # Get grid information
            grid_info = client.search_objects("grid")
            
            # Get member information
            members = client.search_objects("member")
            
            result = {
                "grid_info": grid_info,
                "members": members,
                "member_count": len(members)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get system info: {str(e)}")
    
    @staticmethod
    async def _get_capacity_report(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Get capacity report."""
        try:
            params = {}
            if "member_name" in args:
                params["member"] = args["member_name"]
            
            capacity_reports = client.search_objects("capacityreport", params)
            
            result = {
                "capacity_reports": capacity_reports,
                "count": len(capacity_reports)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting capacity report: {str(e)}")
            raise InfoBloxAPIError(f"Failed to get capacity report: {str(e)}")


class BulkTools:
    """Bulk operations tools for InfoBlox."""
    
    @staticmethod
    def register_tools(registry):
        """Register all bulk operation tools."""
        
        # CSV Import/Export
        registry.register_tool(
            "infoblox_bulk_import_csv",
            "Import data from CSV file",
            {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["INSERT", "UPDATE", "DELETE", "OVERRIDE"],
                        "description": "Import operation type"
                    },
                    "object_type": {
                        "type": "string",
                        "description": "Object type to import (e.g., 'record:a', 'network')"
                    },
                    "csv_data": {
                        "type": "string",
                        "description": "CSV data as string"
                    },
                    "update_policy": {
                        "type": "string",
                        "enum": ["MERGE", "REPLACE"],
                        "description": "Update policy for existing records (optional)"
                    }
                },
                "required": ["operation", "object_type", "csv_data"]
            },
            BulkTools._import_csv
        )
        
        registry.register_tool(
            "infoblox_bulk_export_csv",
            "Export data to CSV format",
            {
                "type": "object",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type to export (e.g., 'record:a', 'network')"
                    },
                    "search_params": {
                        "type": "object",
                        "description": "Search parameters to filter export (optional)",
                        "additionalProperties": True
                    },
                    "return_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to include in export (optional)"
                    }
                },
                "required": ["object_type"]
            },
            BulkTools._export_csv
        )
        
        # Bulk Record Operations
        registry.register_tool(
            "infoblox_bulk_create_a_records",
            "Create multiple A records from a list",
            {
                "type": "object",
                "properties": {
                    "records": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "ipv4addr": {"type": "string"},
                                "view": {"type": "string"},
                                "ttl": {"type": "integer"},
                                "comment": {"type": "string"}
                            },
                            "required": ["name", "ipv4addr"]
                        },
                        "description": "List of A records to create"
                    }
                },
                "required": ["records"]
            },
            BulkTools._bulk_create_a_records
        )
        
        registry.register_tool(
            "infoblox_bulk_delete_records",
            "Delete multiple records by reference",
            {
                "type": "object",
                "properties": {
                    "record_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of record references to delete"
                    }
                },
                "required": ["record_refs"]
            },
            BulkTools._bulk_delete_records
        )
    
    @staticmethod
    async def _import_csv(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Import CSV data."""
        try:
            import_data = {
                "operation": args["operation"],
                "object_type": args["object_type"],
                "csv_data": args["csv_data"]
            }
            
            if "update_policy" in args:
                import_data["update_policy"] = args["update_policy"]
            
            # Create CSV import task
            import_ref = client.create_object("csvimporttask", import_data)
            
            result = {
                "success": True,
                "import_reference": import_ref,
                "operation": args["operation"],
                "object_type": args["object_type"]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            raise InfoBloxAPIError(f"Failed to import CSV: {str(e)}")
    
    @staticmethod
    async def _export_csv(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Export data to CSV."""
        try:
            object_type = args["object_type"]
            search_params = args.get("search_params", {})
            return_fields = args.get("return_fields")
            
            # Add CSV return type
            search_params["_return_type"] = "csv"
            if return_fields:
                search_params["_return_fields"] = ",".join(return_fields)
            
            # Get data
            csv_data = client.get(object_type, params=search_params)
            
            result = {
                "object_type": object_type,
                "csv_data": csv_data,
                "export_successful": True
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {str(e)}")
            raise InfoBloxAPIError(f"Failed to export CSV: {str(e)}")
    
    @staticmethod
    async def _bulk_create_a_records(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Bulk create A records."""
        try:
            records = args["records"]
            results = []
            errors = []
            
            for record in records:
                try:
                    record_ref = client.create_object("record:a", record)
                    results.append({
                        "success": True,
                        "record": record,
                        "reference": record_ref
                    })
                except Exception as e:
                    errors.append({
                        "record": record,
                        "error": str(e)
                    })
            
            result = {
                "total_records": len(records),
                "successful": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error bulk creating A records: {str(e)}")
            raise InfoBloxAPIError(f"Failed to bulk create A records: {str(e)}")
    
    @staticmethod
    async def _bulk_delete_records(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Bulk delete records."""
        try:
            record_refs = args["record_refs"]
            results = []
            errors = []
            
            for record_ref in record_refs:
                try:
                    client.delete_object(record_ref)
                    results.append({
                        "success": True,
                        "reference": record_ref
                    })
                except Exception as e:
                    errors.append({
                        "reference": record_ref,
                        "error": str(e)
                    })
            
            result = {
                "total_records": len(record_refs),
                "successful": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error bulk deleting records: {str(e)}")
            raise InfoBloxAPIError(f"Failed to bulk delete records: {str(e)}")


class AnalysisTools:
    """Analysis and reporting tools for InfoBlox."""

    @staticmethod
    def register_tools(registry):
        """Register all analysis tools."""
        
        # AWS PVC Import Analysis
        registry.register_tool(
            "infoblox_aws_import_analysis",
            "Analyze AWS PVC export file for import readiness",
            {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Absolute path to the AWS PVC export file (CSV)"
                    },
                    "network_view": {
                        "type": "string",
                        "description": "Target network view (default: 'default')"
                    }
                },
                "required": ["file_name"]
            },
            AnalysisTools._aws_import_analysis
        )

        # AWS PVC Import Execution
        registry.register_tool(
            "infoblox_aws_import_execute",
            "Import AWS PVC export file (creates networks)",
            {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Absolute path to the AWS PVC export file (CSV)"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate creation without changes (default: true)"
                    },
                    "network_view": {
                        "type": "string",
                        "description": "Target network view (default: 'default')"
                    }
                },
                "required": ["file_name"]
            },
            AnalysisTools._aws_import_execute
        )

        # MARSHA EA Search
        registry.register_tool(
            "infoblox_search_marsha",
            "Search for networks with a specific MARSHA EA value",
            {
                "type": "object",
                "properties": {
                    "marsha_value": {
                        "type": "string",
                        "description": "Value of the MARSHA EA to search for"
                    }
                },
                "required": ["marsha_value"]
            },
            AnalysisTools._search_marsha
        )

    @staticmethod
    async def _search_marsha(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Search by MARSHA EA."""
        try:
            marsha_value = args["marsha_value"]
            
            # 1. Check if MARSHA EA definition exists (optional but good practice)
            # We skip this for speed, relying on the search to fail or return empty if EA doesn't exist
            # but usually *EA search requires the EA to be defined.
            
            # 2. Perform Search
            # In WAPI, searching by EA uses *EA_Name notation
            search_params = {
                "*MARSHA": marsha_value
            }
            
            networks = client.search_objects("network", search_params)
            
            result = {
                "searched_value": marsha_value,
                "count": len(networks),
                "networks": networks
            }
            
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error searching by MARSHA EA: {str(e)}")
            raise InfoBloxAPIError(f"Failed to search by MARSHA EA: {str(e)}")

    @staticmethod
    async def _aws_import_execute(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Execute AWS PVC import."""
        # Reuse analysis logic implicitly or duplicated for now to keep it clean, 
        # but execution adds creation step.
        # Ideally we refactor common logic, but to avoid breaking existing tool, copy-modify is safer for now
        # given the constraint of minimizing risk.
        
        file_name = args["file_name"]
        file_name = args["file_name"]
        dry_run = args.get("dry_run", True)
        network_view = args.get("network_view", "default")
        
        results = {
            "total_records": 0,
            "valid_records": 0,
            "conflicts": [],
            "missing_eas": set(),
            "created_networks": [],
            "errors": []
        }

        try:
            # 1. Fetch valid EAs
            try:
                eas_resp = client.search_objects("extensibleattributedef")
                valid_eas = {ea["name"] for ea in eas_resp}
            except Exception:
                valid_eas = set() # Proceed with empty set (will mark all as missing)

            standard_aws_columns = {"AccountId", "Region", "VpcId", "Name"}
            
            with open(file_name, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                required_cols = ["CidrBlock", "Tags"]
                if not all(col in reader.fieldnames for col in required_cols):
                    return json.dumps({"error": "Missing required columns"})

                for row in reader:
                    results["total_records"] += 1
                    cidr = row.get("CidrBlock")
                    tags_str = row.get("Tags")
                    
                    if not cidr: continue

                    # Check existence
                    search_params = {"network": cidr}
                    if network_view:
                        search_params["network_view"] = network_view
                    existing_nets = client.search_objects("network", search_params)
                    if existing_nets:
                        results["conflicts"].append({"network": cidr, "reason": "Exists"})
                        continue
                    
                    # Prepare EAs
                    record_eas = {} # Dict for creation {Name: Value}
                    
                    # Columns
                    for col in standard_aws_columns:
                        val = row.get(col)
                        if val:
                             if not valid_eas or col in valid_eas:
                                 record_eas[col] = val
                             else:
                                 results["missing_eas"].add(col)
                    
                    # Tags
                    if tags_str:
                        try:
                            tags_list = ast.literal_eval(tags_str)
                            if isinstance(tags_list, list):
                                for tag in tags_list:
                                    if isinstance(tag, dict) and 'Key' in tag:
                                        key = tag['Key']
                                        val = tag.get('Value', "")
                                        if not valid_eas or key in valid_eas:
                                            record_eas[key] = val
                                        else:
                                            results["missing_eas"].add(key)
                        except Exception:
                            pass # Parse error ignored for execution flow, just won't add tags

                    # Create Network
                    if not dry_run:
                        try:
                            network_data = {
                                "network": cidr,
                                "network_view": network_view,
                                "extensible_attributes": record_eas,
                                "comment": "Imported from AWS PVC"
                            }
                            # InfoBlox WAPI uses "network" object for IPv4
                            client.create_object("network", network_data)
                            results["created_networks"].append(cidr)
                        except Exception as e:
                            results["errors"].append({"network": cidr, "error": str(e)})
                    else:
                        # In dry run, we assume success if we got here
                        results["valid_records"] += 1

            results["missing_eas"] = list(results["missing_eas"])
            return json.dumps(results, indent=2)

        except Exception as e:
            raise InfoBloxAPIError(f"Import execution failed: {e}")


    @staticmethod
    async def _aws_import_analysis(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Analyze AWS PVC export file."""
        try:
            file_name = args["file_name"]
            network_view = args.get("network_view", "default")
            
            # Fetch valid InfoBlox EAs
            try:
                # We need to get all extensible attributes definitions to validate mapping
                # Since there might be many, we'll fetch them all.
                # In a real large scale environment, we might want to cache this or be more selective.
                # extensibleattributedef is the WAPI object for EA definitions
                eas_resp = client.search_objects("extensibleattributedef")
                valid_eas = {ea["name"] for ea in eas_resp}
            except Exception as e:
                logger.warning(f"Could not fetch EA definitions: {e}. detailed validation disabled.")
                valid_eas = set()

            analysis_results = {
                "total_records": 0,
                "valid_records": 0,
                "conflicts": [],
                "missing_eas": set(),
                "mapped_eas": set()
            }
            
            # Standard AWS columns we might want to map to EAs if they exist in IB
            standard_aws_columns = {"AccountId", "Region", "VpcId", "Name"}
            
            with open(file_name, 'r', encoding='utf-8') as csvfile:
                # Use DictReader to handle headers automatically
                reader = csv.DictReader(csvfile)
                
                # Check for required columns
                required_cols = ["CidrBlock", "Tags"]
                if not all(col in reader.fieldnames for col in required_cols):
                    return json.dumps({"error": f"Missing required columns. Found: {reader.fieldnames}, Expected at least: {required_cols}"})

                for row in reader:
                    analysis_results["total_records"] += 1
                    cidr = row.get("CidrBlock")
                    tags_str = row.get("Tags")
                    
                    if not cidr:
                        continue # Skip invalid rows

                    # 1. Network Conflict Analysis
                    # Check if network exists
                    search_params = {"network": cidr}
                    if network_view:
                        search_params["network_view"] = network_view
                        
                    existing_nets = client.search_objects("network", search_params)
                    if existing_nets:
                        # Extract network view from the found network
                        net_view = existing_nets[0].get("network_view", "unknown")
                        analysis_results["conflicts"].append({
                            "network": cidr,
                            "reason": "Network already exists",
                            "network_view": net_view,
                            "target_view": network_view,
                            "ref": existing_nets[0]["_ref"]
                        })
                    
                    # 2. EA Analysis
                    current_record_eas = set()
                    
                    # Process Standard Columns as potential EAs
                    for col in standard_aws_columns:
                        if col in row and row[col]:
                             if not valid_eas or col in valid_eas:
                                 current_record_eas.add(col)
                             else:
                                 analysis_results["missing_eas"].add(col)

                    # Process Tags
                    if tags_str:
                        try:
                            # Tags is typically "Key=Value;Key=Value" or JSON-like
                            # Based on user input: "[{'Key': '...', 'Value': '...'}]"
                            # We use ast.literal_eval for safe parsing of python-like string structures
                            tags_list = ast.literal_eval(tags_str)
                            
                            if isinstance(tags_list, list):
                                for tag in tags_list:
                                    if isinstance(tag, dict) and 'Key' in tag:
                                        key = tag['Key']
                                        if not valid_eas or key in valid_eas:
                                            current_record_eas.add(key)
                                        else:
                                            analysis_results["missing_eas"].add(key)
                        except (ValueError, SyntaxError) as e:
                            logger.warning(f"Failed to parse tags for {cidr}: {e}")
                    
                    analysis_results["mapped_eas"].update(current_record_eas)
                    
                    # If no conflict, we count as valid for now (even if EAs are missing, they just won't be imported)
                    if not existing_nets:
                         analysis_results["valid_records"] += 1

            # Convert sets to lists for JSON serialization
            analysis_results["missing_eas"] = list(analysis_results["missing_eas"])
            analysis_results["mapped_eas"] = list(analysis_results["mapped_eas"])
            
            return json.dumps(analysis_results, indent=2)

        except FileNotFoundError:
             raise InfoBloxAPIError(f"File not found: {file_name}")
        except Exception as e:
            logger.error(f"Error analyzing AWS import: {str(e)}")
            raise InfoBloxAPIError(f"Failed to analyze AWS import: {str(e)}")
