"""
Response Formatter for Open WebUI Integration

This module formats InfoBlox MCP responses for better display in Open WebUI.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FormattedResponse:
    """Formatted response for Open WebUI."""
    content: str
    content_type: str = "markdown"
    metadata: Optional[Dict[str, Any]] = None


class ResponseFormatter:
    """Formatter for InfoBlox MCP responses."""
    
    def __init__(self):
        """Initialize the response formatter."""
        self.formatters = {
            "infoblox_ipam_get_network_utilization": self._format_network_utilization,
            "infoblox_dns_list_zones": self._format_dns_zones,
            "infoblox_dns_search_records": self._format_dns_records,
            "infoblox_dhcp_list_networks": self._format_dhcp_networks,
            "infoblox_dhcp_get_next_available_ip": self._format_next_available_ips,
            "infoblox_dhcp_list_leases": self._format_dhcp_leases,
            "infoblox_dhcp_get_network_details": self._format_network_details,
            "infoblox_grid_list_members": self._format_grid_members,
            "infoblox_grid_get_status": self._format_grid_status,
            "infoblox_bulk_export_csv": self._format_bulk_export,
        }
    
    def format_response(self, tool_name: str, response_data: Any, execution_time: float = None) -> FormattedResponse:
        """
        Format a response based on the tool used.
        
        Args:
            tool_name: Name of the tool that was executed
            response_data: Raw response data from the tool
            execution_time: Time taken to execute the tool
            
        Returns:
            FormattedResponse object
        """
        try:
            # Get specific formatter or use default
            formatter = self.formatters.get(tool_name, self._format_default)
            
            # Format the response
            formatted_content = formatter(response_data)
            
            # Add execution metadata
            if execution_time:
                formatted_content += f"\n\n---\n*Executed in {execution_time:.2f}s*"
            
            return FormattedResponse(
                content=formatted_content,
                content_type="markdown",
                metadata={
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return FormattedResponse(
                content=f"**Error formatting response:** {str(e)}\n\n**Raw data:**\n```json\n{json.dumps(response_data, indent=2)}\n```",
                content_type="markdown"
            )
    
    def _format_network_utilization(self, data: Any) -> str:
        """Format network utilization response."""
        if isinstance(data, dict):
            network = data.get("network", "Unknown")
            utilization = data.get("utilization", {})
            
            content = f"## 📊 Network Utilization: {network}\n\n"
            
            if isinstance(utilization, dict):
                total_ips = utilization.get("total_ips", 0)
                used_ips = utilization.get("used_ips", 0)
                available_ips = utilization.get("available_ips", 0)
                utilization_percent = utilization.get("utilization_percent", 0)
                
                # Create a visual progress bar
                bar_length = 20
                filled_length = int(bar_length * utilization_percent / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                
                content += f"**Utilization:** {utilization_percent:.1f}%\n"
                content += f"`{bar}` {used_ips}/{total_ips} IPs\n\n"
                content += f"| Metric | Value |\n"
                content += f"|--------|-------|\n"
                content += f"| Total IPs | {total_ips:,} |\n"
                content += f"| Used IPs | {used_ips:,} |\n"
                content += f"| Available IPs | {available_ips:,} |\n"
                content += f"| Utilization | {utilization_percent:.1f}% |\n"
                
                # Add status indicator
                if utilization_percent > 90:
                    content += f"\n🔴 **High utilization warning!**"
                elif utilization_percent > 75:
                    content += f"\n🟡 **Medium utilization**"
                else:
                    content += f"\n🟢 **Normal utilization**"
            else:
                content += f"```json\n{json.dumps(data, indent=2)}\n```"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_dns_zones(self, data: Any) -> str:
        """Format DNS zones list."""
        if isinstance(data, dict) and "zones" in data:
            zones = data["zones"]
            count = data.get("count", len(zones) if isinstance(zones, list) else 0)
            
            content = f"## 🌐 DNS Zones ({count} found)\n\n"
            
            if isinstance(zones, list) and zones:
                content += "| Zone Name | Type | View | Records |\n"
                content += "|-----------|------|------|----------|\n"
                
                for zone in zones:
                    name = zone.get("fqdn", "Unknown")
                    zone_type = zone.get("zone_format", "Unknown")
                    view = zone.get("view", "default")
                    record_count = zone.get("record_count", "N/A")
                    content += f"| {name} | {zone_type} | {view} | {record_count} |\n"
            else:
                content += "*No zones found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_dns_records(self, data: Any) -> str:
        """Format DNS records search results."""
        if isinstance(data, dict) and "records" in data:
            records = data["records"]
            count = data.get("count", len(records) if isinstance(records, list) else 0)
            
            content = f"## 📝 DNS Records ({count} found)\n\n"
            
            if isinstance(records, list) and records:
                content += "| Name | Type | Value | TTL | View |\n"
                content += "|------|------|-------|-----|------|\n"
                
                for record in records:
                    name = record.get("name", "Unknown")
                    record_type = record.get("type", "Unknown")
                    value = record.get("value", record.get("ipv4addr", record.get("ipv6addr", "Unknown")))
                    ttl = record.get("ttl", "Default")
                    view = record.get("view", "default")
                    content += f"| {name} | {record_type} | {value} | {ttl} | {view} |\n"
            else:
                content += "*No records found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_dhcp_networks(self, data: Any) -> str:
        """Format DHCP networks list."""
        if isinstance(data, dict) and "networks" in data:
            networks = data["networks"]
            count = data.get("count", len(networks) if isinstance(networks, list) else 0)
            
            content = f"## 🔌 DHCP Networks ({count} found)\n\n"
            
            if isinstance(networks, list) and networks:
                content += "| Network | Netmask | Gateway | DHCP Enabled | Comment |\n"
                content += "|---------|---------|---------|--------------|----------|\n"
                
                for network in networks:
                    net_addr = network.get("network", "Unknown")
                    netmask = network.get("netmask", "Unknown")
                    gateway = network.get("gateway", "N/A")
                    dhcp_enabled = "✅" if network.get("dhcp_enabled", False) else "❌"
                    comment = network.get("comment", "")[:50] + ("..." if len(network.get("comment", "")) > 50 else "")
                    content += f"| {net_addr} | {netmask} | {gateway} | {dhcp_enabled} | {comment} |\n"
            else:
                content += "*No networks found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_next_available_ips(self, data: Any) -> str:
        """Format next available IPs."""
        if isinstance(data, dict) and "available_ips" in data:
            ips = data["available_ips"]
            network = data.get("network", "Unknown")
            
            content = f"## 🆓 Next Available IPs in {network}\n\n"
            
            if isinstance(ips, list) and ips:
                content += "| IP Address | Status |\n"
                content += "|------------|--------|\n"
                
                for ip in ips:
                    content += f"| {ip} | Available |\n"
                
                content += f"\n**Total available IPs shown:** {len(ips)}"
            else:
                content += "*No available IPs found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_dhcp_leases(self, data: Any) -> str:
        """Format DHCP leases."""
        if isinstance(data, dict) and "leases" in data:
            leases = data["leases"]
            count = data.get("count", len(leases) if isinstance(leases, list) else 0)
            
            content = f"## 📋 DHCP Leases ({count} active)\n\n"
            
            if isinstance(leases, list) and leases:
                content += "| IP Address | MAC Address | Client Name | Lease End | State |\n"
                content += "|------------|-------------|-------------|-----------|-------|\n"
                
                for lease in leases:
                    ip = lease.get("ip_address", "Unknown")
                    mac = lease.get("mac_address", "Unknown")
                    client = lease.get("client_hostname", "Unknown")
                    lease_end = lease.get("ends", "Unknown")
                    state = lease.get("binding_state", "Unknown")
                    content += f"| {ip} | {mac} | {client} | {lease_end} | {state} |\n"
            else:
                content += "*No active leases found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_network_details(self, data: Any) -> str:
        """Format network details."""
        if isinstance(data, dict):
            network = data.get("network", "Unknown")
            
            content = f"## 🔍 Network Details: {network}\n\n"
            
            # Basic information
            content += "### Basic Information\n"
            content += f"- **Network:** {data.get('network', 'N/A')}\n"
            content += f"- **Netmask:** {data.get('netmask', 'N/A')}\n"
            content += f"- **Gateway:** {data.get('gateway', 'N/A')}\n"
            content += f"- **DHCP Enabled:** {'Yes' if data.get('dhcp_enabled', False) else 'No'}\n"
            content += f"- **Comment:** {data.get('comment', 'None')}\n\n"
            
            # Extended attributes
            if "extattrs" in data and data["extattrs"]:
                content += "### Extended Attributes\n"
                content += "| Attribute | Value |\n"
                content += "|-----------|-------|\n"
                
                for attr, value in data["extattrs"].items():
                    if isinstance(value, dict) and "value" in value:
                        value = value["value"]
                    content += f"| {attr} | {value} |\n"
                content += "\n"
            
            # DHCP options
            if "options" in data and data["options"]:
                content += "### DHCP Options\n"
                content += "| Option | Value |\n"
                content += "|--------|-------|\n"
                
                for option in data["options"]:
                    name = option.get("name", "Unknown")
                    value = option.get("value", "Unknown")
                    content += f"| {name} | {value} |\n"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_grid_members(self, data: Any) -> str:
        """Format grid members list."""
        if isinstance(data, dict) and "members" in data:
            members = data["members"]
            count = data.get("count", len(members) if isinstance(members, list) else 0)
            
            content = f"## ⚙️ Grid Members ({count} found)\n\n"
            
            if isinstance(members, list) and members:
                content += "| Member Name | IP Address | Platform | Status | Services |\n"
                content += "|-------------|------------|----------|--------|----------|\n"
                
                for member in members:
                    name = member.get("host_name", "Unknown")
                    ip = member.get("vip_setting", {}).get("address", "Unknown")
                    platform = member.get("platform", "Unknown")
                    status = "🟢 Online" if member.get("node_info", [{}])[0].get("status") == "ONLINE" else "🔴 Offline"
                    services = ", ".join(member.get("service_type_configuration", []))
                    content += f"| {name} | {ip} | {platform} | {status} | {services} |\n"
            else:
                content += "*No grid members found*"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_grid_status(self, data: Any) -> str:
        """Format grid status."""
        if isinstance(data, dict):
            content = f"## 📊 Grid System Status\n\n"
            
            status = data.get("status", "Unknown")
            status_icon = "🟢" if status == "ONLINE" else "🔴"
            
            content += f"**Overall Status:** {status_icon} {status}\n\n"
            
            if "details" in data:
                details = data["details"]
                content += "### System Details\n"
                content += f"- **Version:** {details.get('version', 'Unknown')}\n"
                content += f"- **Uptime:** {details.get('uptime', 'Unknown')}\n"
                content += f"- **Load Average:** {details.get('load_average', 'Unknown')}\n"
                content += f"- **Memory Usage:** {details.get('memory_usage', 'Unknown')}\n"
                content += f"- **Disk Usage:** {details.get('disk_usage', 'Unknown')}\n"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_bulk_export(self, data: Any) -> str:
        """Format bulk export results."""
        if isinstance(data, dict):
            content = f"## 📤 Bulk Export Results\n\n"
            
            if data.get("success", False):
                content += "✅ **Export completed successfully**\n\n"
                content += f"- **Records exported:** {data.get('record_count', 'Unknown')}\n"
                content += f"- **File location:** {data.get('file_path', 'Unknown')}\n"
                content += f"- **Format:** {data.get('format', 'CSV')}\n"
            else:
                content += "❌ **Export failed**\n\n"
                content += f"**Error:** {data.get('error', 'Unknown error')}\n"
        else:
            content = f"```json\n{json.dumps(data, indent=2)}\n```"
        
        return content
    
    def _format_default(self, data: Any) -> str:
        """Default formatter for unknown response types."""
        if isinstance(data, dict):
            content = "## 📋 Response\n\n"
            
            # Try to format as a simple table if it's a list of objects
            if isinstance(data, dict) and len(data) == 1:
                key, value = next(iter(data.items()))
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    content += f"### {key.replace('_', ' ').title()}\n\n"
                    
                    # Get all unique keys from all objects
                    all_keys = set()
                    for item in value:
                        all_keys.update(item.keys())
                    
                    # Create table
                    headers = list(all_keys)[:5]  # Limit to 5 columns
                    content += "| " + " | ".join(headers) + " |\n"
                    content += "|" + "|".join(["---"] * len(headers)) + "|\n"
                    
                    for item in value[:10]:  # Limit to 10 rows
                        row = []
                        for header in headers:
                            value = str(item.get(header, ""))[:50]  # Limit cell content
                            row.append(value)
                        content += "| " + " | ".join(row) + " |\n"
                    
                    if len(value) > 10:
                        content += f"\n*... and {len(value) - 10} more items*\n"
                    
                    return content
            
            # Fallback to JSON
            content += f"```json\n{json.dumps(data, indent=2)}\n```"
        else:
            content = f"```\n{str(data)}\n```"
        
        return content
