"""
Intent Recognition System for InfoBlox Natural Language Queries

This module analyzes natural language queries and maps them to specific InfoBlox MCP tools.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Categories of user intents."""
    DNS_QUERY = "dns_query"
    DHCP_QUERY = "dhcp_query"
    IPAM_QUERY = "ipam_query"
    GRID_QUERY = "grid_query"
    BULK_OPERATION = "bulk_operation"
    CREATE_OPERATION = "create_operation"
    DELETE_OPERATION = "delete_operation"
    UPDATE_OPERATION = "update_operation"
    LIST_OPERATION = "list_operation"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a recognized user intent."""
    category: IntentCategory
    action: str
    tool_name: str
    parameters: Dict[str, Any]
    confidence: float
    raw_query: str


class IntentRecognitionEngine:
    """Engine for recognizing user intents from natural language."""
    
    def __init__(self):
        """Initialize the intent recognition engine."""
        self.patterns = self._build_patterns()
        self.tool_mappings = self._build_tool_mappings()
    
    def _build_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build regex patterns for intent recognition."""
        return {
            # Network/IPAM patterns
            "network_utilization": [
                {
                    "pattern": r"(?:show|get|check)\s+(?:network\s+)?(?:utilization|usage)\s+(?:for\s+)?([0-9./]+)",
                    "tool": "infoblox_ipam_get_network_utilization",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:utilization|usage)\s+(?:of\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_ipam_get_network_utilization", 
                    "params": {"network": 1}
                }
            ],
            
            # DNS patterns
            "dns_zones": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:all\s+)?(?:dns\s+)?zones?",
                    "tool": "infoblox_dns_list_zones",
                    "params": {}
                },
                {
                    "pattern": r"(?:what|which)\s+(?:dns\s+)?zones?\s+(?:are\s+)?(?:available|exist)",
                    "tool": "infoblox_dns_list_zones",
                    "params": {}
                }
            ],
            
            "dns_records": [
                {
                    "pattern": r"(?:find|search|get|show)\s+(?:dns\s+)?(?:a\s+)?records?\s+(?:for\s+)?([a-zA-Z0-9.-]+)",
                    "tool": "infoblox_dns_search_records",
                    "params": {"record_type": "A", "name": 1}
                },
                {
                    "pattern": r"(?:find|search|get|show)\s+([a-zA-Z]+)\s+records?\s+(?:for\s+)?([a-zA-Z0-9.-]+)",
                    "tool": "infoblox_dns_search_records",
                    "params": {"record_type": 1, "name": 2}
                }
            ],
            
            # DHCP patterns
            "dhcp_networks": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:all\s+)?(?:dhcp\s+)?networks?",
                    "tool": "infoblox_dhcp_list_networks",
                    "params": {}
                },
                {
                    "pattern": r"(?:what|which)\s+(?:dhcp\s+)?networks?\s+(?:are\s+)?(?:available|configured)",
                    "tool": "infoblox_dhcp_list_networks",
                    "params": {}
                }
            ],
            
            "next_available_ip": [
                {
                    "pattern": r"(?:get|find|show)\s+(?:next\s+)?available\s+ips?\s+(?:in\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_get_next_available_ip",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:next|available)\s+ips?\s+(?:for\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_get_next_available_ip",
                    "params": {"network": 1}
                }
            ],
            
            "dhcp_leases": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:active\s+)?(?:dhcp\s+)?leases?",
                    "tool": "infoblox_dhcp_list_leases",
                    "params": {}
                },
                {
                    "pattern": r"(?:leases?)\s+(?:for\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_list_leases",
                    "params": {"network": 1}
                }
            ],
            
            # Grid patterns
            "grid_members": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:grid\s+)?members?",
                    "tool": "infoblox_grid_list_members",
                    "params": {}
                },
                {
                    "pattern": r"(?:what|which)\s+(?:grid\s+)?members?\s+(?:are\s+)?(?:available|online)",
                    "tool": "infoblox_grid_list_members",
                    "params": {}
                }
            ],
            
            "grid_status": [
                {
                    "pattern": r"(?:get|show|check)\s+(?:grid\s+)?status",
                    "tool": "infoblox_grid_get_status",
                    "params": {}
                },
                {
                    "pattern": r"(?:system|grid)\s+(?:health|status)",
                    "tool": "infoblox_grid_get_status",
                    "params": {}
                }
            ],
            
            # Network details patterns
            "network_details": [
                {
                    "pattern": r"(?:show|get|describe)\s+(?:network\s+)?([0-9./]+)\s+(?:details|info|information)",
                    "tool": "infoblox_dhcp_get_network_details",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:details|info|information)\s+(?:about\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_get_network_details",
                    "params": {"network": 1}
                }
            ],
            
            # Extended attributes patterns
            "extended_attributes": [
                {
                    "pattern": r"(?:show|get)\s+(?:network\s+)?([0-9./]+)\s+(?:extended\s+)?attributes?",
                    "tool": "infoblox_dhcp_get_network_details",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:extended\s+)?attributes?\s+(?:for\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_get_network_details",
                    "params": {"network": 1}
                }
            ]
        }
    
    def _build_tool_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build mappings between tools and their metadata."""
        return {
            "infoblox_ipam_get_network_utilization": {
                "category": IntentCategory.IPAM_QUERY,
                "action": "get_utilization",
                "required_params": ["network"]
            },
            "infoblox_dns_list_zones": {
                "category": IntentCategory.DNS_QUERY,
                "action": "list_zones",
                "required_params": []
            },
            "infoblox_dns_search_records": {
                "category": IntentCategory.DNS_QUERY,
                "action": "search_records",
                "required_params": ["record_type"]
            },
            "infoblox_dhcp_list_networks": {
                "category": IntentCategory.DHCP_QUERY,
                "action": "list_networks",
                "required_params": []
            },
            "infoblox_dhcp_get_next_available_ip": {
                "category": IntentCategory.DHCP_QUERY,
                "action": "get_next_ip",
                "required_params": ["network"]
            },
            "infoblox_dhcp_list_leases": {
                "category": IntentCategory.DHCP_QUERY,
                "action": "list_leases",
                "required_params": []
            },
            "infoblox_grid_list_members": {
                "category": IntentCategory.GRID_QUERY,
                "action": "list_members",
                "required_params": []
            },
            "infoblox_grid_get_status": {
                "category": IntentCategory.GRID_QUERY,
                "action": "get_status",
                "required_params": []
            },
            "infoblox_dhcp_get_network_details": {
                "category": IntentCategory.DHCP_QUERY,
                "action": "get_network_details",
                "required_params": ["network"]
            }
        }
    
    def recognize_intent(self, query: str) -> Optional[Intent]:
        """
        Recognize intent from a natural language query.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Intent object if recognized, None otherwise
        """
        query_lower = query.lower().strip()
        
        # Try to match patterns
        for intent_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                tool_name = pattern_info["tool"]
                param_mapping = pattern_info["params"]
                
                match = re.search(pattern, query_lower)
                if match:
                    # Extract parameters
                    parameters = {}
                    for param_name, group_index in param_mapping.items():
                        if isinstance(group_index, int) and group_index <= len(match.groups()):
                            parameters[param_name] = match.group(group_index)
                        elif isinstance(group_index, str):
                            parameters[param_name] = group_index
                    
                    # Get tool metadata
                    tool_info = self.tool_mappings.get(tool_name, {})
                    category = tool_info.get("category", IntentCategory.UNKNOWN)
                    action = tool_info.get("action", "unknown")
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_confidence(pattern, query_lower)
                    
                    return Intent(
                        category=category,
                        action=action,
                        tool_name=tool_name,
                        parameters=parameters,
                        confidence=confidence,
                        raw_query=query
                    )
        
        return None
    
    def _calculate_confidence(self, pattern: str, query: str) -> float:
        """Calculate confidence score for a pattern match."""
        # Simple confidence calculation based on pattern complexity
        # and query length
        pattern_complexity = len(pattern.split())
        query_length = len(query.split())
        
        # Base confidence
        confidence = 0.7
        
        # Boost for more specific patterns
        if pattern_complexity > 3:
            confidence += 0.1
        
        # Boost for exact keyword matches
        keywords = ["network", "dns", "dhcp", "zone", "record", "lease", "utilization"]
        keyword_matches = sum(1 for keyword in keywords if keyword in query)
        confidence += keyword_matches * 0.05
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def get_suggestions(self, query: str) -> List[str]:
        """Get suggestions for improving unclear queries."""
        suggestions = []
        
        query_lower = query.lower()
        
        # Check for partial matches and suggest completions
        if "network" in query_lower:
            if not re.search(r"[0-9./]+", query):
                suggestions.append("Please specify a network address (e.g., 192.168.1.0/24)")
            
            if "utilization" not in query_lower and "details" not in query_lower:
                suggestions.extend([
                    "Try: 'show network X.X.X.X/XX utilization'",
                    "Try: 'show network X.X.X.X/XX details'"
                ])
        
        if "dns" in query_lower:
            suggestions.extend([
                "Try: 'list dns zones'",
                "Try: 'find A records for domain.com'"
            ])
        
        if "dhcp" in query_lower:
            suggestions.extend([
                "Try: 'list dhcp networks'",
                "Try: 'get next available IP in 192.168.1.0/24'"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions
