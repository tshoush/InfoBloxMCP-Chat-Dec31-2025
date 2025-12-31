"""AWS PVC Import tools for InfoBlox MCP Server."""

import json
import logging
from typing import Any, Dict, List, Optional
from .client import InfoBloxClient, InfoBloxAPIError
import csv
import ast

logger = logging.getLogger(__name__)

class AWSImportTools:
    """Tools for importing AWS PVC data into InfoBlox."""

    @staticmethod
    def register_tools(registry):
        """Register all AWS Import tools."""
        
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
            AWSImportTools._aws_import_analysis
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
            AWSImportTools._aws_import_execute
        )

    @staticmethod
    async def _aws_import_analysis(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Analyze AWS PVC export file."""
        try:
            file_name = args["file_name"]
            network_view = args.get("network_view", "default")
            
            # Fetch valid InfoBlox EAs
            try:
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
            
            standard_aws_columns = {"AccountId", "Region", "VpcId", "Name"}
            
            with open(file_name, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                required_cols = ["CidrBlock", "Tags"]
                if not all(col in reader.fieldnames for col in required_cols):
                    return json.dumps({"error": f"Missing required columns. Found: {reader.fieldnames}, Expected at least: {required_cols}"})

                for row in reader:
                    analysis_results["total_records"] += 1
                    cidr = row.get("CidrBlock")
                    tags_str = row.get("Tags")
                    
                    if not cidr:
                        continue 

                    # 1. Network Conflict Analysis
                    search_params = {"network": cidr}
                    if network_view:
                        search_params["network_view"] = network_view
                        
                    existing_nets = client.search_objects("network", search_params)
                    if existing_nets:
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
                    
                    for col in standard_aws_columns:
                        if col in row and row[col]:
                             if not valid_eas or col in valid_eas:
                                 current_record_eas.add(col)
                             else:
                                 analysis_results["missing_eas"].add(col)

                    if tags_str:
                        try:
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
                    
                    if not existing_nets:
                         analysis_results["valid_records"] += 1

            analysis_results["missing_eas"] = list(analysis_results["missing_eas"])
            analysis_results["mapped_eas"] = list(analysis_results["mapped_eas"])
            
            return json.dumps(analysis_results, indent=2)

        except FileNotFoundError:
             raise InfoBloxAPIError(f"File not found: {file_name}")
        except Exception as e:
            logger.error(f"Error analyzing AWS import: {str(e)}")
            raise InfoBloxAPIError(f"Failed to analyze AWS import: {str(e)}")

    @staticmethod
    async def _aws_import_execute(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """Execute AWS PVC import."""
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
            try:
                eas_resp = client.search_objects("extensibleattributedef")
                valid_eas = {ea["name"] for ea in eas_resp}
            except Exception:
                valid_eas = set()

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

                    search_params = {"network": cidr}
                    if network_view:
                        search_params["network_view"] = network_view
                    existing_nets = client.search_objects("network", search_params)
                    if existing_nets:
                        results["conflicts"].append({"network": cidr, "reason": "Exists"})
                        continue
                    
                    record_eas = {} 
                    
                    for col in standard_aws_columns:
                        val = row.get(col)
                        if val:
                             if not valid_eas or col in valid_eas:
                                 record_eas[col] = val
                             else:
                                 results["missing_eas"].add(col)
                    
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
                            pass

                    if not dry_run:
                        try:
                            network_data = {
                                "network": cidr,
                                "network_view": network_view,
                                "extensible_attributes": record_eas,
                                "comment": "Imported from AWS PVC"
                            }
                            client.create_object("network", network_data)
                            results["created_networks"].append(cidr)
                        except Exception as e:
                            results["errors"].append({"network": cidr, "error": str(e)})
                    else:
                        results["valid_records"] += 1

            results["missing_eas"] = list(results["missing_eas"])
            return json.dumps(results, indent=2)

        except Exception as e:
            raise InfoBloxAPIError(f"Import execution failed: {e}")
