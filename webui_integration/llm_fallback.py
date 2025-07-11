"""
LLM Fallback Handler for Complex Query Interpretation

This module uses various LLM APIs to interpret complex queries that couldn't be
handled by the intent recognition system.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import openai
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    api_key: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.1


@dataclass
class LLMInterpretation:
    """Result from LLM interpretation."""
    tool_name: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    provider_used: LLMProvider


class LLMFallbackHandler:
    """Handler for LLM-based query interpretation."""
    
    def __init__(self, llm_configs: List[LLMConfig]):
        """
        Initialize the LLM fallback handler.
        
        Args:
            llm_configs: List of LLM configurations to try
        """
        self.llm_configs = llm_configs
        self.tool_descriptions = self._load_tool_descriptions()
    
    def _load_tool_descriptions(self) -> str:
        """Load InfoBlox tool descriptions for LLM context."""
        return """
Available InfoBlox MCP Tools:

DNS TOOLS:
- infoblox_dns_list_zones: List all DNS zones
- infoblox_dns_create_zone: Create a new DNS zone (params: fqdn, view?, comment?)
- infoblox_dns_search_records: Search DNS records (params: record_type, name?, ip_address?, view?, zone?)
- infoblox_dns_create_record_a: Create A record (params: name, ipv4addr, view?, ttl?, comment?)
- infoblox_dns_create_record_aaaa: Create AAAA record (params: name, ipv6addr, view?, ttl?, comment?)
- infoblox_dns_create_record_cname: Create CNAME record (params: name, canonical, view?, ttl?, comment?)
- infoblox_dns_delete_record: Delete DNS record (params: record_ref)
- infoblox_dns_update_record: Update DNS record (params: record_ref, updates)

DHCP TOOLS:
- infoblox_dhcp_list_networks: List all DHCP networks
- infoblox_dhcp_create_network: Create DHCP network (params: network, network_view?, comment?)
- infoblox_dhcp_get_next_available_ip: Get next available IPs (params: network, num_ips?)
- infoblox_dhcp_get_network_details: Get network details (params: network)
- infoblox_dhcp_list_leases: List DHCP leases (params: network?, ip_address?, mac_address?, client_hostname?)
- infoblox_dhcp_create_fixed_address: Create fixed address (params: ipv4addr, mac?, name?, comment?)
- infoblox_dhcp_list_fixed_addresses: List fixed addresses (params: network?, mac?)
- infoblox_dhcp_create_range: Create DHCP range (params: start_addr, end_addr, network?, comment?)

IPAM TOOLS:
- infoblox_ipam_get_network_utilization: Get network utilization (params: network)
- infoblox_ipam_discover_networks: Discover networks (params: network_view?, discovery_member?)
- infoblox_ipam_scan_network: Scan network for hosts (params: network, scan_type?)
- infoblox_ipam_find_next_available_network: Find next available subnet (params: container, cidr, num_networks?)
- infoblox_ipam_get_utilization_summary: Get utilization summary (params: network_view?, threshold?)

GRID TOOLS:
- infoblox_grid_list_members: List grid members
- infoblox_grid_get_status: Get grid status
- infoblox_grid_get_member_details: Get member details (params: member_name)
- infoblox_grid_restart_services: Restart services (params: member_name, service_option?)
- infoblox_grid_backup_database: Create backup (params: backup_type?, comment?)

BULK TOOLS:
- infoblox_bulk_create_a_records: Bulk create A records (params: records)
- infoblox_bulk_export_csv: Export to CSV (params: object_type, search_params?, return_fields?)
"""
    
    async def interpret_query(self, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """
        Interpret a complex query using LLM providers.
        
        Args:
            query: User's natural language query
            available_tools: List of available tool names (optional)
            
        Returns:
            LLMInterpretation if successful, None otherwise
        """
        for config in self.llm_configs:
            try:
                result = await self._try_provider(config, query, available_tools)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"LLM provider {config.provider.value} failed: {str(e)}")
                continue
        
        logger.error("All LLM providers failed to interpret query")
        return None
    
    async def _try_provider(self, config: LLMConfig, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """Try a specific LLM provider."""
        if config.provider == LLMProvider.OPENAI:
            return await self._try_openai(config, query, available_tools)
        elif config.provider == LLMProvider.ANTHROPIC:
            return await self._try_anthropic(config, query, available_tools)
        elif config.provider == LLMProvider.GROQ:
            return await self._try_groq(config, query, available_tools)
        elif config.provider == LLMProvider.TOGETHER:
            return await self._try_together(config, query, available_tools)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def _try_openai(self, config: LLMConfig, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """Try OpenAI API."""
        client = openai.AsyncOpenAI(api_key=config.api_key)
        
        prompt = self._build_prompt(query, available_tools)
        
        try:
            response = await client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": "You are an expert at interpreting InfoBlox network management queries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content, LLMProvider.OPENAI)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def _try_anthropic(self, config: LLMConfig, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """Try Anthropic API."""
        client = AsyncAnthropic(api_key=config.api_key)
        
        prompt = self._build_prompt(query, available_tools)
        
        try:
            response = await client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return self._parse_llm_response(content, LLMProvider.ANTHROPIC)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    async def _try_groq(self, config: LLMConfig, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """Try Groq API."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = self._build_prompt(query, available_tools)
        
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "You are an expert at interpreting InfoBlox network management queries."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        return self._parse_llm_response(content, LLMProvider.GROQ)
                    else:
                        raise Exception(f"Groq API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise
    
    async def _try_together(self, config: LLMConfig, query: str, available_tools: List[str] = None) -> Optional[LLMInterpretation]:
        """Try Together AI API."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = self._build_prompt(query, available_tools)
        
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "You are an expert at interpreting InfoBlox network management queries."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        return self._parse_llm_response(content, LLMProvider.TOGETHER)
                    else:
                        raise Exception(f"Together API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Together API error: {str(e)}")
            raise
    
    def _build_prompt(self, query: str, available_tools: List[str] = None) -> str:
        """Build prompt for LLM interpretation."""
        tools_context = self.tool_descriptions
        if available_tools:
            tools_context += f"\n\nCurrently available tools: {', '.join(available_tools)}"
        
        return f"""
{tools_context}

User Query: "{query}"

Please analyze this query and determine:
1. Which InfoBlox tool should be used
2. What parameters are needed
3. Your confidence level (0.0-1.0)
4. Your reasoning

Respond in this exact JSON format:
{{
    "tool_name": "exact_tool_name",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "confidence": 0.85,
    "reasoning": "explanation of why this tool and parameters were chosen"
}}

Important:
- Use exact tool names from the list above
- Extract network addresses, IP addresses, hostnames, etc. from the query
- If the query is ambiguous, choose the most likely interpretation
- Set confidence lower for ambiguous queries
"""
    
    def _parse_llm_response(self, content: str, provider: LLMProvider) -> Optional[LLMInterpretation]:
        """Parse LLM response into structured format."""
        try:
            # Try to extract JSON from the response
            content = content.strip()
            
            # Find JSON block
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON found in LLM response")
                return None
            
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["tool_name", "parameters", "confidence", "reasoning"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            return LLMInterpretation(
                tool_name=data["tool_name"],
                parameters=data["parameters"],
                confidence=float(data["confidence"]),
                reasoning=data["reasoning"],
                provider_used=provider
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None
