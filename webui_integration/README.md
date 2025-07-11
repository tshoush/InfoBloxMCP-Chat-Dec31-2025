# InfoBlox Open WebUI Integration

This integration provides natural language access to InfoBlox DDI (DNS, DHCP, IPAM) management through Open WebUI. Users can query InfoBlox systems using plain English instead of complex API calls.

## 🚀 Features

- **Natural Language Processing**: Query InfoBlox using plain English
- **Intent Recognition**: Automatically recognizes common InfoBlox operations
- **LLM Fallback**: Uses multiple LLM providers for complex query interpretation
- **Rich Formatting**: Beautiful tables and charts in Open WebUI
- **54 InfoBlox Tools**: Access to all InfoBlox MCP server capabilities

## 📋 Quick Start

### 1. Prerequisites

- InfoBlox MCP Server running and configured
- Open WebUI instance
- At least one LLM API key (OpenAI, Anthropic, Groq, or Together AI)

### 2. Installation

**Option A: Simple Installation (Recommended)**

1. Copy `infoblox_function.py` to your Open WebUI functions directory
2. Set environment variables for API keys
3. Import the function in Open WebUI

**Option B: Full Installation**

1. Install dependencies:
```bash
pip install -r webui_integration/requirements.txt
```

2. Copy the entire `webui_integration` directory to your project
3. Configure environment variables
4. Import the main function

### 3. Configuration

Set the following environment variables:

```bash
# Required: InfoBlox MCP Server
export INFOBLOX_MCP_SERVER_PATH="python3 /path/to/infoblox-mcp-server.py"

# Optional: LLM API Keys (at least one recommended)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GROQ_API_KEY="your-groq-key"
export TOGETHER_API_KEY="your-together-key"
```

### 4. Open WebUI Setup

1. Copy `infoblox_function.py` to your Open WebUI functions directory
2. Restart Open WebUI
3. The function will be automatically available as `infoblox_query`

## 🎯 Usage Examples

### Network Operations
```
"show network 192.168.1.0/24 utilization"
"get network 10.0.0.0/8 details"
"show network 172.16.0.0/16 extended attributes"
```

### DNS Operations
```
"list all DNS zones"
"find A records for example.com"
"show DNS zones in default view"
```

### DHCP Operations
```
"list DHCP networks"
"get next available IPs in 192.168.1.0/24"
"show DHCP leases for network 10.0.0.0/24"
"list active DHCP leases"
```

### Grid Operations
```
"list grid members"
"show grid status"
"get grid member details for member1"
```

### IPAM Operations
```
"show utilization summary"
"discover networks in default view"
"scan network 192.168.1.0/24 for hosts"
```

## 🏗️ Architecture

```
User Query → Intent Recognition → MCP Tool Execution → Response Formatting
     ↓              ↓                      ↓                    ↓
"show network   Recognized as      infoblox_ipam_get_     Formatted table
utilization"    utilization query   network_utilization   with progress bar
     ↓
LLM Fallback (if intent unclear)
```

### Components

1. **Intent Recognition Engine**: Pattern-based recognition for common queries
2. **LLM Fallback Handler**: Multiple LLM providers for complex interpretation
3. **MCP Client**: Communicates with InfoBlox MCP server
4. **Response Formatter**: Creates beautiful tables and visualizations

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INFOBLOX_MCP_SERVER_PATH` | Path to InfoBlox MCP server | `python3 infoblox-mcp-server.py` |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `GROQ_API_KEY` | Groq API key | None |
| `TOGETHER_API_KEY` | Together AI API key | None |

### Advanced Configuration

Create `webui_config.json` for advanced settings:

```json
{
  "mcp_server_path": "python3 /path/to/infoblox-mcp-server.py",
  "mcp_server_timeout": 30,
  "intent_confidence_threshold": 0.6,
  "llm_confidence_threshold": 0.5,
  "max_table_rows": 20,
  "log_level": "INFO"
}
```

## 📊 Response Formats

### Network Utilization
```
## 📊 Network Utilization: 192.168.1.0/24

**Utilization:** 75.5%
`███████████████░░░░░` 192/254 IPs

| Metric | Value |
|--------|-------|
| Total IPs | 254 |
| Used IPs | 192 |
| Available IPs | 62 |
| Utilization | 75.5% |
```

### DNS Zones
```
## 🌐 DNS Zones (3 found)

| Zone Name | Type | View |
|-----------|------|------|
| example.com | FORWARD | default |
| test.local | FORWARD | internal |
| 1.168.192.in-addr.arpa | IPV4_REVERSE | default |
```

## 🧪 Testing

### Test the Integration

```python
# Test basic functionality
result = await infoblox_query("list DNS zones")
print(result)

# Test network utilization
result = await infoblox_query("show network 192.168.1.0/24 utilization")
print(result)

# Test LLM fallback
result = await infoblox_query("what networks do we have configured?")
print(result)
```

### Validate Configuration

```python
from webui_integration.config import config_manager

# Check configuration
issues = config_manager.validate_config()
if issues:
    print("Configuration issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Configuration is valid")

# Check available LLM providers
providers = config_manager.get_available_llm_providers()
print(f"Available LLM providers: {providers}")
```

## 🔍 Troubleshooting

### Common Issues

1. **"MCP server not found"**
   - Check `INFOBLOX_MCP_SERVER_PATH` environment variable
   - Ensure InfoBlox MCP server is accessible
   - Verify server is running and configured

2. **"No LLM providers available"**
   - Set at least one LLM API key environment variable
   - Check API key validity
   - Verify network connectivity to LLM providers

3. **"Query not understood"**
   - Try more specific language
   - Use suggested query formats
   - Check if the operation is supported

4. **"Tool execution failed"**
   - Check InfoBlox MCP server logs
   - Verify InfoBlox connection and credentials
   - Ensure network/resource exists

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL="DEBUG"
```

### Manual Testing

Test individual components:

```python
# Test intent recognition
from webui_integration.intent_recognition import IntentRecognitionEngine
engine = IntentRecognitionEngine()
intent = engine.recognize_intent("show network 192.168.1.0/24 utilization")
print(intent)

# Test MCP client
from webui_integration.mcp_client import InfoBloxMCPClient
async with InfoBloxMCPClient() as client:
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
```

## 📚 API Reference

### Main Function

```python
async def infoblox_query(query: str) -> str:
    """
    Query InfoBlox DDI system using natural language.
    
    Args:
        query: Natural language query
        
    Returns:
        Formatted response string
    """
```

### Supported Query Types

- **Network Utilization**: `show network X.X.X.X/XX utilization`
- **Network Details**: `show network X.X.X.X/XX details`
- **DNS Zones**: `list DNS zones`
- **DNS Records**: `find A records for domain.com`
- **DHCP Networks**: `list DHCP networks`
- **Available IPs**: `get next available IPs in X.X.X.X/XX`
- **DHCP Leases**: `show DHCP leases`
- **Grid Members**: `list grid members`
- **Grid Status**: `show grid status`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Check the troubleshooting section
- Review InfoBlox MCP server logs
- Open an issue on GitHub
- Check Open WebUI documentation

---

**Note**: This integration requires a running InfoBlox MCP server and appropriate InfoBlox system access.
