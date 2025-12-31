
import json
import logging
from typing import Dict, Any, List

from .client import InfoBloxClient
from .config import InfoBloxConfig
from .splunk_client import SplunkClient

logger = logging.getLogger(__name__)

class SplunkTools:
    """Tools for interacting with Splunk."""

    @staticmethod
    def register_tools(registry):
        """Register Splunk tools."""
        
        registry.register_tool(
            "infoblox_splunk_audit_search",
            "Search Splunk for InfoBlox audit history",
            {
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "Name of the object to search for (e.g., network CIDR, zone name)"
                    },
                    "action": {
                        "type": "string",
                        "description": "Optional action filter (e.g., 'create', 'delete')"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to search back (default: 30)"
                    }
                },
                "required": ["object_name"]
            },
            SplunkTools._search_audit_history
        )

    @staticmethod
    async def _search_audit_history(args: Dict[str, Any], client: InfoBloxClient) -> str:
        """
        Search Splunk for audit logs related to an object.
        Note: The 'client' arg passed by the MCP framework is InfoBloxClient, 
        but we need SplunkClient. We will init SplunkClient from the same config.
        """
        try:
            object_name = args["object_name"]
            action = args.get("action")
            days_back = args.get("days_back", 30)
            
            # Init Splunk Client
            # client.config should be available
            splunk_client = SplunkClient(client.config)
            
            # Construct Query
            # Assuming standard InfoBlox Splunk Add-on sourcetype "infoblox:audit"
            # Adjust index if necessary, often 'index=*' or 'index=infoblox'
            query = f'search index=* (sourcetype="infoblox:audit" OR sourcetype="infoblox:nios:audit") "{object_name}"'
            
            if action:
                query += f' action="*{action}*"'
                
            query += " | table _time, admin_name, action, object_type, object_name, _raw"
            query += " | sort -_time"
            
            logger.info(f"Running Splunk query for {object_name}")
            results = splunk_client.search(
                query, 
                earliest_time=f"-{days_back}d", 
                latest_time="now"
            )
            
            response = {
                "object_name": object_name,
                "days_back": days_back,
                "count": len(results),
                "events": results
            }
            
            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})
