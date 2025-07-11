"""
InfoBlox Open WebUI Function

This is the main function file that can be directly imported into Open WebUI
to provide natural language access to InfoBlox DDI management.

Installation:
1. Copy this file to your Open WebUI functions directory
2. Set environment variables for API keys
3. Ensure InfoBlox MCP server is accessible
4. Import the function in Open WebUI

Usage Examples:
- "show network 192.168.1.0/24 utilization"
- "list all DNS zones"
- "get next available IPs in 10.0.0.0/24"
- "show DHCP leases for network 172.16.0.0/16"
"""

import asyncio
import json
import logging
import os
import subprocess
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class InfoBloxWebUIFunction:
    """Main InfoBlox function for Open WebUI."""
    
    def __init__(self):
        """Initialize the function."""
        self.mcp_server_path = os.getenv("INFOBLOX_MCP_SERVER_PATH", "python3 infoblox-mcp-server.py")
        self.patterns = self._build_patterns()
        self.llm_configs = self._get_llm_configs()
    
    def _build_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build regex patterns for intent recognition."""
        return {
            "network_utilization": [
                {
                    "pattern": r"(?:show|get|check)\s+(?:network\s+)?(?:utilization|usage)\s+(?:for\s+)?([0-9./]+)",
                    "tool": "infoblox_ipam_get_network_utilization",
                    "params": {"network": 1}
                }
            ],
            "dns_zones": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:all\s+)?(?:dns\s+)?zones?",
                    "tool": "infoblox_dns_list_zones",
                    "params": {}
                }
            ],
            "dhcp_networks": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:all\s+)?(?:dhcp\s+)?networks?",
                    "tool": "infoblox_dhcp_list_networks",
                    "params": {}
                }
            ],
            "next_available_ip": [
                {
                    "pattern": r"(?:get|find|show)\s+(?:next\s+)?available\s+ips?\s+(?:in\s+)?(?:network\s+)?([0-9./]+)",
                    "tool": "infoblox_dhcp_get_next_available_ip",
                    "params": {"network": 1}
                }
            ],
            "dhcp_leases": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:active\s+)?(?:dhcp\s+)?leases?",
                    "tool": "infoblox_dhcp_list_leases",
                    "params": {}
                }
            ],
            "grid_members": [
                {
                    "pattern": r"(?:list|show|get)\s+(?:grid\s+)?members?",
                    "tool": "infoblox_grid_list_members",
                    "params": {}
                }
            ],
            "network_details": [
                {
                    "pattern": r"(?:show|get|describe)\s+(?:network\s+)?([0-9./]+)\s+(?:details|info|information|attributes)",
                    "tool": "infoblox_dhcp_get_network_details",
                    "params": {"network": 1}
                }
            ],
            "network_utilization": [
                {
                    "pattern": r"(?:show|get|display)\s+(?:network\s+)?(?:utilization|usage)\s*(?:for\s+)?([0-9./]+)",
                    "tool": "infoblox_ipam_get_network_utilization",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:show|get|display)\s+(?:network\s+)?([0-9./]+)\s+(?:utilization|usage)",
                    "tool": "infoblox_ipam_get_network_utilization",
                    "params": {"network": 1}
                },
                {
                    "pattern": r"(?:show|get|display)\s+(?:network\s+)?(?:utilization|usage)(?:\s+(?:all|summary))?$",
                    "tool": "infoblox_ipam_get_network_utilization",
                    "params": {"network": "192.168.100.0/24"}
                }
            ]
        }
    
    def _get_llm_configs(self) -> List[Dict[str, str]]:
        """Get available LLM configurations."""
        configs = []
        
        if os.getenv("OPENAI_API_KEY"):
            configs.append({
                "provider": "openai",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o-mini"
            })
        
        if os.getenv("ANTHROPIC_API_KEY"):
            configs.append({
                "provider": "anthropic", 
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-haiku-20240307"
            })
        
        if os.getenv("GROQ_API_KEY"):
            configs.append({
                "provider": "groq",
                "api_key": os.getenv("GROQ_API_KEY"),
                "model": "llama-3.1-8b-instant"
            })
        
        return configs
    
    def recognize_intent(self, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Recognize intent from natural language query."""
        query_lower = query.lower().strip()
        
        for intent_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                tool_name = pattern_info["tool"]
                param_mapping = pattern_info["params"]
                
                match = re.search(pattern, query_lower)
                if match:
                    parameters = {}
                    for param_name, group_index in param_mapping.items():
                        if isinstance(group_index, int) and group_index <= len(match.groups()):
                            parameters[param_name] = match.group(group_index)
                    
                    return tool_name, parameters
        
        return None
    
    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool via subprocess communication."""
        try:
            # For this simplified version, we'll use a direct approach
            # In production, you might want to use a persistent connection

            # Import the InfoBlox MCP components directly
            import sys
            import os

            # Add the InfoBlox MCP server path to Python path
            mcp_server_dir = os.path.dirname(self.mcp_server_path.replace("python3 ", ""))
            if mcp_server_dir:
                sys.path.insert(0, mcp_server_dir)

            # Try to import and use the MCP client directly
            try:
                from src.infoblox_mcp.client import InfoBloxClient
                from src.infoblox_mcp.config import ConfigManager
                from src.infoblox_mcp.tools import ToolRegistry

                # Load configuration
                config_manager = ConfigManager()
                config = config_manager.load_config()

                if not config:
                    return {"success": False, "error": "InfoBlox MCP server not configured"}

                # Execute tool directly
                registry = ToolRegistry()

                with InfoBloxClient(config) as client:
                    result = await registry.execute_tool(tool_name, parameters, client)

                    # Parse result
                    try:
                        data = json.loads(result)
                        return {"success": True, "data": data}
                    except json.JSONDecodeError:
                        return {"success": True, "data": result}

            except ImportError:
                # Fallback to subprocess approach
                return await self._execute_via_subprocess(tool_name, parameters)

        except Exception as e:
            logger.error(f"Tool execution error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_via_subprocess(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method using subprocess."""
        try:
            # This is a simplified approach - in production you'd want a more robust IPC mechanism
            import tempfile

            # Create a temporary script to execute the tool
            script_content = f"""
import sys
import os
import json
import asyncio

# Add MCP server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.client import InfoBloxClient
from infoblox_mcp.config import ConfigManager
from infoblox_mcp.tools import ToolRegistry

async def main():
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()

        if not config:
            print(json.dumps({{"success": False, "error": "Not configured"}}))
            return

        registry = ToolRegistry()

        with InfoBloxClient(config) as client:
            result = await registry.execute_tool("{tool_name}", {json.dumps(parameters)}, client)

            try:
                data = json.loads(result)
                print(json.dumps({{"success": True, "data": data}}))
            except json.JSONDecodeError:
                print(json.dumps({{"success": True, "data": result}}))

    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))

if __name__ == "__main__":
    asyncio.run(main())
"""

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_script = f.name

            try:
                # Execute the temporary script
                process = subprocess.Popen(
                    ["python3", temp_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(self.mcp_server_path.replace("python3 ", ""))
                )

                stdout, stderr = process.communicate(timeout=30)

                if process.returncode == 0 and stdout:
                    return json.loads(stdout.strip())
                else:
                    return {"success": False, "error": f"Execution failed: {stderr}"}

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_script)
                except:
                    pass

        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def llm_fallback(self, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Use LLM to interpret unclear queries."""
        if not self.llm_configs:
            return None
        
        tools_description = """
Available InfoBlox tools:
- infoblox_ipam_get_network_utilization: Get network utilization (params: network)
- infoblox_dns_list_zones: List DNS zones
- infoblox_dhcp_list_networks: List DHCP networks  
- infoblox_dhcp_get_next_available_ip: Get next available IPs (params: network)
- infoblox_dhcp_list_leases: List DHCP leases
- infoblox_grid_list_members: List grid members
- infoblox_dhcp_get_network_details: Get network details (params: network)
"""
        
        prompt = f"""
{tools_description}

User Query: "{query}"

Analyze this query and respond with JSON:
{{
    "tool_name": "exact_tool_name",
    "parameters": {{"param": "value"}},
    "confidence": 0.85
}}
"""
        
        for config in self.llm_configs:
            try:
                if config["provider"] == "openai":
                    result = await self._try_openai(config, prompt)
                elif config["provider"] == "anthropic":
                    result = await self._try_anthropic(config, prompt)
                elif config["provider"] == "groq":
                    result = await self._try_groq(config, prompt)
                else:
                    continue
                
                if result and result.get("confidence", 0) > 0.5:
                    return result["tool_name"], result["parameters"]
                    
            except Exception as e:
                logger.warning(f"LLM provider {config['provider']} failed: {str(e)}")
                continue
        
        return None
    
    async def _try_openai(self, config: Dict[str, str], prompt: str) -> Optional[Dict[str, Any]]:
        """Try OpenAI API."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=config["api_key"])
            
            response = await client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return None
    
    async def _try_anthropic(self, config: Dict[str, str], prompt: str) -> Optional[Dict[str, Any]]:
        """Try Anthropic API."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=config["api_key"])
            
            response = await client.messages.create(
                model=config["model"],
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self._parse_llm_response(content)
        except Exception as e:
            logger.error(f"Anthropic error: {str(e)}")
            return None
    
    async def _try_groq(self, config: Dict[str, str], prompt: str) -> Optional[Dict[str, Any]]:
        """Try Groq API."""
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        return self._parse_llm_response(content)
            
            return None
        except Exception as e:
            logger.error(f"Groq error: {str(e)}")
            return None
    
    def _parse_llm_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response."""
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        except Exception:
            return None
    
    def format_response(self, tool_name: str, data: Any) -> str:
        """Format response for display."""
        if tool_name == "infoblox_ipam_get_network_utilization":
            return self._format_utilization(data)
        elif tool_name == "infoblox_dns_list_zones":
            return self._format_zones(data)
        elif tool_name == "infoblox_dhcp_list_networks":
            return self._format_networks(data)
        elif tool_name == "infoblox_dhcp_get_next_available_ip":
            return self._format_available_ips(data)
        elif tool_name == "infoblox_dhcp_list_leases":
            return self._format_leases(data)
        elif tool_name == "infoblox_grid_list_members":
            return self._format_members(data)
        elif tool_name == "infoblox_dhcp_get_network_details":
            return self._format_network_details(data)
        else:
            return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_utilization(self, data: Any) -> str:
        """Format network utilization."""
        if isinstance(data, dict) and "utilization" in data:
            util = data["utilization"]
            network = data.get("network", "Unknown")
            percent = util.get("utilization_percent", 0)
            used = util.get("used_ips", 0)
            total = util.get("total_ips", 0)
            
            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            return f"""## 📊 Network Utilization: {network}

**Utilization:** {percent:.1f}%
`{bar}` {used:,}/{total:,} IPs

| Metric | Value |
|--------|-------|
| Total IPs | {total:,} |
| Used IPs | {used:,} |
| Available IPs | {total - used:,} |
| Utilization | {percent:.1f}% |
"""
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_zones(self, data: Any) -> str:
        """Format DNS zones."""
        if isinstance(data, dict) and "zones" in data:
            zones = data["zones"]
            count = len(zones) if isinstance(zones, list) else 0
            
            content = f"## 🌐 DNS Zones ({count} found)\n\n"
            
            if zones:
                content += "| Zone Name | Type | View |\n|-----------|------|------|\n"
                for zone in zones[:10]:
                    name = zone.get("fqdn", "Unknown")
                    zone_type = zone.get("zone_format", "Unknown")
                    view = zone.get("view", "default")
                    content += f"| {name} | {zone_type} | {view} |\n"
            else:
                content += "*No zones found*"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_networks(self, data: Any) -> str:
        """Format DHCP networks."""
        if isinstance(data, dict) and "networks" in data:
            networks = data["networks"]
            count = len(networks) if isinstance(networks, list) else 0
            
            content = f"## 🔌 DHCP Networks ({count} found)\n\n"
            
            if networks:
                content += "| Network | Gateway | DHCP |\n|---------|---------|------|\n"
                for net in networks[:10]:
                    network = net.get("network", "Unknown")
                    gateway = net.get("gateway", "N/A")
                    dhcp = "✅" if net.get("dhcp_enabled", False) else "❌"
                    content += f"| {network} | {gateway} | {dhcp} |\n"
            else:
                content += "*No networks found*"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_available_ips(self, data: Any) -> str:
        """Format available IPs."""
        if isinstance(data, dict) and "available_ips" in data:
            ips = data["available_ips"]
            network = data.get("network", "Unknown")
            
            content = f"## 🆓 Next Available IPs in {network}\n\n"
            
            if ips:
                content += "| IP Address |\n|------------|\n"
                for ip in ips[:10]:
                    content += f"| {ip} |\n"
                content += f"\n**Total available IPs shown:** {len(ips)}"
            else:
                content += "*No available IPs found*"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_leases(self, data: Any) -> str:
        """Format DHCP leases."""
        if isinstance(data, dict) and "leases" in data:
            leases = data["leases"]
            count = len(leases) if isinstance(leases, list) else 0
            
            content = f"## 📋 DHCP Leases ({count} active)\n\n"
            
            if leases:
                content += "| IP Address | MAC Address | Client |\n|------------|-------------|--------|\n"
                for lease in leases[:10]:
                    ip = lease.get("ip_address", "Unknown")
                    mac = lease.get("mac_address", "Unknown")
                    client = lease.get("client_hostname", "Unknown")
                    content += f"| {ip} | {mac} | {client} |\n"
            else:
                content += "*No active leases found*"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_members(self, data: Any) -> str:
        """Format grid members."""
        if isinstance(data, dict) and "members" in data:
            members = data["members"]
            count = len(members) if isinstance(members, list) else 0
            
            content = f"## ⚙️ Grid Members ({count} found)\n\n"
            
            if members:
                content += "| Member Name | IP Address | Status |\n|-------------|------------|--------|\n"
                for member in members:
                    name = member.get("host_name", "Unknown")
                    ip = member.get("vip_setting", {}).get("address", "Unknown")
                    status = "🟢 Online" if member.get("node_info", [{}])[0].get("status") == "ONLINE" else "🔴 Offline"
                    content += f"| {name} | {ip} | {status} |\n"
            else:
                content += "*No grid members found*"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_network_details(self, data: Any) -> str:
        """Format network details."""
        if isinstance(data, dict):
            network = data.get("network", "Unknown")
            
            content = f"## 🔍 Network Details: {network}\n\n"
            content += f"- **Network:** {data.get('network', 'N/A')}\n"
            content += f"- **Netmask:** {data.get('netmask', 'N/A')}\n"
            content += f"- **Gateway:** {data.get('gateway', 'N/A')}\n"
            content += f"- **DHCP Enabled:** {'Yes' if data.get('dhcp_enabled', False) else 'No'}\n"
            content += f"- **Comment:** {data.get('comment', 'None')}\n"
            
            if "extattrs" in data and data["extattrs"]:
                content += "\n### Extended Attributes\n"
                content += "| Attribute | Value |\n|-----------|-------|\n"
                for attr, value in data["extattrs"].items():
                    if isinstance(value, dict) and "value" in value:
                        value = value["value"]
                    content += f"| {attr} | {value} |\n"
            
            return content
        return f"```json\n{json.dumps(data, indent=2)}\n```"


# Global function instance
infoblox_func = InfoBloxWebUIFunction()


async def infoblox_query(query: str) -> str:
    """
    Query InfoBlox DDI system using natural language.
    
    This function provides natural language access to InfoBlox management
    through the MCP server.
    
    Args:
        query: Natural language query (e.g., "show network 192.168.1.0/24 utilization")
        
    Returns:
        Formatted response string
        
    Examples:
        - "show network 192.168.1.0/24 utilization"
        - "list all DNS zones"
        - "get next available IPs in 10.0.0.0/24"
        - "show DHCP leases"
        - "list grid members"
        - "show network 192.168.1.0/24 extended attributes"
    """
    try:
        start_time = time.time()
        
        # Step 1: Try intent recognition
        intent_result = infoblox_func.recognize_intent(query)
        
        if intent_result:
            tool_name, parameters = intent_result
            logger.info(f"Intent recognized: {tool_name}")
        else:
            # Step 2: Try LLM fallback
            logger.info("Intent unclear, trying LLM fallback")
            llm_result = await infoblox_func.llm_fallback(query)
            
            if llm_result:
                tool_name, parameters = llm_result
                logger.info(f"LLM interpreted: {tool_name}")
            else:
                return f"""❓ **Query not understood:** {query}

**Suggestions:**
• Try: 'show network X.X.X.X/XX utilization'
• Try: 'list DNS zones'
• Try: 'get next available IPs in X.X.X.X/XX'
• Try: 'show DHCP leases'
• Try: 'list grid members'"""
        
        # Step 3: Execute the tool
        result = await infoblox_func.execute_mcp_tool(tool_name, parameters)
        execution_time = time.time() - start_time
        
        if result["success"]:
            formatted_response = infoblox_func.format_response(tool_name, result["data"])
            formatted_response += f"\n\n---\n*Executed in {execution_time:.2f}s*"
            return formatted_response
        else:
            return f"❌ **Tool execution failed:** {result['error']}"
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return f"❌ **Error processing query:** {str(e)}"


# Function metadata for Open WebUI
def get_function_metadata():
    """Get function metadata for Open WebUI registration."""
    return {
        "name": "infoblox_query",
        "description": "Query InfoBlox DDI system using natural language. Supports DNS, DHCP, IPAM, and Grid operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query for InfoBlox operations"
                }
            },
            "required": ["query"]
        }
    }
