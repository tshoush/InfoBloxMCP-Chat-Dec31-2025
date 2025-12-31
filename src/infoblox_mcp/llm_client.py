
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from .config import InfoBloxConfig
from mcp.types import Tool

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with LLM APIs (OpenAI Compatible)."""
    
    def __init__(self, config: InfoBloxConfig):
        """Initialize LLM client."""
        self.config = config
        self.api_key = config.llm_api_key
        self.model = config.llm_model or "gpt-4o"
        self.base_url = config.llm_base_url or "https://api.openai.com/v1"
        
        if not self.base_url.rstrip('/').endswith('/v1'):
             # normalizing base url if needed, though strictly v1 might not be required for some local servers
             pass

    def is_configured(self) -> bool:
        """Check if LLM is configured."""
        return bool(self.api_key)

    def generate_response(self, user_message: str, mcp_tools: List[Tool]) -> Dict[str, Any]:
        """
        Send message to LLM and get response (Text or Tool Call).
        """
        if not self.is_configured():
            return {"type": "error", "content": "LLM not configured."}

        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Convert MCP Tools to OpenAI Tools format
        openai_tools = []
        for tool in mcp_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful InfoBlox Network Assistant. You help users manage DNS, DHCP, and IPAM. Use the provided tools to answer user questions. dealing with IPs, networks, zones, and Splunk logs. If the user asks for historical data or 'who did what', use the splunk/history tools."
                },
                {"role": "user", "content": user_message}
            ],
            "tools": openai_tools,
            "tool_choice": "auto"
        }
        
        try:
            logger.info(f"Calling LLM: {self.model} with message: {user_message[:50]}...")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            choice = data['choices'][0]
            message = choice['message']
            
            if message.get("tool_calls"):
                tool_call = message["tool_calls"][0]
                function = tool_call["function"]
                return {
                    "type": "tool_call",
                    "tool_name": function["name"],
                    "tool_args": json.loads(function["arguments"])
                }
            else:
                return {
                    "type": "text",
                    "content": message.get("content", "")
                }
                
        except Exception as e:
            logger.error(f"LLM Call Failed: {e}")
            return {"type": "error", "content": f"LLM error: {str(e)}"}
