"""
Open WebUI Function for InfoBlox MCP Integration

This is the main function that integrates with Open WebUI to provide natural language
access to InfoBlox management through the MCP server.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Import our custom modules
from .mcp_client import InfoBloxMCPClient, MCPResponse
from .intent_recognition import IntentRecognitionEngine, Intent, IntentCategory
from .llm_fallback import LLMFallbackHandler, LLMConfig, LLMProvider
from .response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class InfoBloxQuery(BaseModel):
    """Input model for InfoBlox queries."""
    query: str = Field(..., description="Natural language query for InfoBlox operations")
    use_llm_fallback: bool = Field(default=True, description="Whether to use LLM fallback for unclear queries")


class InfoBloxResponse(BaseModel):
    """Response model for InfoBlox queries."""
    success: bool
    content: str
    tool_used: Optional[str] = None
    intent_recognized: bool = False
    llm_used: Optional[str] = None
    execution_time: Optional[float] = None
    suggestions: Optional[List[str]] = None


class InfoBloxMCPFunction:
    """Main function class for Open WebUI integration."""
    
    def __init__(self):
        """Initialize the InfoBlox MCP function."""
        self.intent_engine = IntentRecognitionEngine()
        self.response_formatter = ResponseFormatter()
        self.llm_handler = None
        self._initialize_llm_handler()
    
    def _initialize_llm_handler(self):
        """Initialize LLM handler with available API keys."""
        llm_configs = []
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            llm_configs.append(LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini",
                max_tokens=1000,
                temperature=0.1
            ))
        
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            llm_configs.append(LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.1
            ))
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            llm_configs.append(LLMConfig(
                provider=LLMProvider.GROQ,
                api_key=os.getenv("GROQ_API_KEY"),
                model="llama-3.1-8b-instant",
                max_tokens=1000,
                temperature=0.1
            ))
        
        # Together AI
        if os.getenv("TOGETHER_API_KEY"):
            llm_configs.append(LLMConfig(
                provider=LLMProvider.TOGETHER,
                api_key=os.getenv("TOGETHER_API_KEY"),
                model="meta-llama/Llama-3-8b-chat-hf",
                max_tokens=1000,
                temperature=0.1
            ))
        
        if llm_configs:
            self.llm_handler = LLMFallbackHandler(llm_configs)
            logger.info(f"Initialized LLM handler with {len(llm_configs)} providers")
        else:
            logger.warning("No LLM API keys found. LLM fallback will be disabled.")
    
    async def process_query(self, query_input: InfoBloxQuery) -> InfoBloxResponse:
        """
        Process a natural language query for InfoBlox operations.
        
        Args:
            query_input: InfoBloxQuery containing the user's natural language query
            
        Returns:
            InfoBloxResponse with formatted results
        """
        query = query_input.query.strip()
        
        if not query:
            return InfoBloxResponse(
                success=False,
                content="❌ **Error:** Empty query provided.",
                suggestions=["Try asking about network utilization, DNS zones, or DHCP networks"]
            )
        
        logger.info(f"Processing query: {query}")
        
        try:
            # Step 1: Try intent recognition
            intent = self.intent_engine.recognize_intent(query)
            
            if intent and intent.confidence > 0.6:
                # Intent recognized with good confidence
                logger.info(f"Intent recognized: {intent.tool_name} (confidence: {intent.confidence})")
                return await self._execute_with_intent(intent)
            
            elif query_input.use_llm_fallback and self.llm_handler:
                # Step 2: Use LLM fallback for unclear queries
                logger.info("Intent unclear, trying LLM fallback")
                return await self._execute_with_llm_fallback(query)
            
            else:
                # Step 3: Provide suggestions for unclear queries
                suggestions = self.intent_engine.get_suggestions(query)
                return InfoBloxResponse(
                    success=False,
                    content=f"❓ **Query not understood:** {query}\n\n**Suggestions:**\n" + 
                           "\n".join([f"• {suggestion}" for suggestion in suggestions]),
                    intent_recognized=False,
                    suggestions=suggestions
                )
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return InfoBloxResponse(
                success=False,
                content=f"❌ **Error processing query:** {str(e)}",
                suggestions=["Please check your query and try again"]
            )
    
    async def _execute_with_intent(self, intent: Intent) -> InfoBloxResponse:
        """Execute a query using recognized intent."""
        try:
            async with InfoBloxMCPClient() as client:
                # Execute the tool
                response = await client.execute_tool(intent.tool_name, intent.parameters)
                
                if response.success:
                    # Format the response
                    formatted = self.response_formatter.format_response(
                        intent.tool_name, 
                        response.data, 
                        response.execution_time
                    )
                    
                    return InfoBloxResponse(
                        success=True,
                        content=formatted.content,
                        tool_used=intent.tool_name,
                        intent_recognized=True,
                        execution_time=response.execution_time
                    )
                else:
                    return InfoBloxResponse(
                        success=False,
                        content=f"❌ **Tool execution failed:** {response.error}",
                        tool_used=intent.tool_name,
                        intent_recognized=True
                    )
        
        except Exception as e:
            logger.error(f"Error executing intent: {str(e)}")
            return InfoBloxResponse(
                success=False,
                content=f"❌ **Execution error:** {str(e)}",
                tool_used=intent.tool_name,
                intent_recognized=True
            )
    
    async def _execute_with_llm_fallback(self, query: str) -> InfoBloxResponse:
        """Execute a query using LLM fallback."""
        try:
            # Get available tools
            async with InfoBloxMCPClient() as client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
            
            # Use LLM to interpret the query
            interpretation = await self.llm_handler.interpret_query(query, tool_names)
            
            if not interpretation:
                return InfoBloxResponse(
                    success=False,
                    content=f"❓ **Could not interpret query:** {query}\n\n" +
                           "Please try rephrasing your request or use more specific terms.",
                    llm_used="failed"
                )
            
            if interpretation.confidence < 0.5:
                return InfoBloxResponse(
                    success=False,
                    content=f"❓ **Low confidence interpretation:** {query}\n\n" +
                           f"**Best guess:** {interpretation.tool_name}\n" +
                           f"**Reasoning:** {interpretation.reasoning}\n\n" +
                           "Please try rephrasing for better results.",
                    llm_used=interpretation.provider_used.value
                )
            
            # Execute the interpreted tool
            async with InfoBloxMCPClient() as client:
                response = await client.execute_tool(
                    interpretation.tool_name, 
                    interpretation.parameters
                )
                
                if response.success:
                    # Format the response
                    formatted = self.response_formatter.format_response(
                        interpretation.tool_name, 
                        response.data, 
                        response.execution_time
                    )
                    
                    # Add LLM interpretation info
                    llm_info = f"\n\n---\n*Interpreted by {interpretation.provider_used.value} " + \
                              f"(confidence: {interpretation.confidence:.1f})*\n" + \
                              f"*Reasoning: {interpretation.reasoning}*"
                    
                    return InfoBloxResponse(
                        success=True,
                        content=formatted.content + llm_info,
                        tool_used=interpretation.tool_name,
                        intent_recognized=False,
                        llm_used=interpretation.provider_used.value,
                        execution_time=response.execution_time
                    )
                else:
                    return InfoBloxResponse(
                        success=False,
                        content=f"❌ **Tool execution failed:** {response.error}\n\n" +
                               f"**LLM interpretation:** {interpretation.tool_name}\n" +
                               f"**Reasoning:** {interpretation.reasoning}",
                        tool_used=interpretation.tool_name,
                        llm_used=interpretation.provider_used.value
                    )
        
        except Exception as e:
            logger.error(f"Error in LLM fallback: {str(e)}")
            return InfoBloxResponse(
                success=False,
                content=f"❌ **LLM fallback error:** {str(e)}",
                llm_used="error"
            )


# Global function instance
infoblox_function = InfoBloxMCPFunction()


async def infoblox_query(query: str, use_llm_fallback: bool = True) -> str:
    """
    Main function for Open WebUI integration.
    
    This function provides natural language access to InfoBlox management
    through the MCP server.
    
    Args:
        query: Natural language query (e.g., "show network 192.168.1.0/24 utilization")
        use_llm_fallback: Whether to use LLM fallback for unclear queries
        
    Returns:
        Formatted response string
    """
    query_input = InfoBloxQuery(query=query, use_llm_fallback=use_llm_fallback)
    response = await infoblox_function.process_query(query_input)
    return response.content


# Open WebUI Function Metadata
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
                    "description": "Natural language query for InfoBlox operations (e.g., 'show network 192.168.1.0/24 utilization', 'list DNS zones', 'get next available IPs in 10.0.0.0/24')"
                },
                "use_llm_fallback": {
                    "type": "boolean",
                    "description": "Whether to use LLM fallback for unclear queries",
                    "default": True
                }
            },
            "required": ["query"]
        },
        "examples": [
            "show network 192.168.1.0/24 utilization",
            "list all DNS zones",
            "get next available IPs in 10.0.0.0/24",
            "show DHCP leases for network 172.16.0.0/16",
            "list grid members",
            "get network 192.168.1.0/24 extended attributes"
        ]
    }
