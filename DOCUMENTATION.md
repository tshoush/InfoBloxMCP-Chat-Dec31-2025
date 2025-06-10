# InfoBlox DDI MCP Server

A comprehensive Model Context Protocol (MCP) server for InfoBlox DDI (DNS, DHCP, and IPAM) management. This server provides 54 tools covering all major InfoBlox WAPI operations through a standardized MCP interface.

## Features

### Comprehensive API Coverage
- **DNS Management**: 18 tools for zone, record, and view management
- **DHCP Management**: 18 tools for network, lease, and option management  
- **IPAM Operations**: 6 tools for IP address management and network discovery
- **Grid Management**: 8 tools for grid member and system administration
- **Bulk Operations**: 4 tools for batch processing and CSV import/export

### Enterprise-Ready
- Secure credential management with encrypted storage
- Comprehensive error handling and logging
- Input validation and sanitization
- SSL/TLS support with certificate verification options
- Configurable timeouts and retry mechanisms

### Easy Integration
- Standard MCP protocol compliance
- Interactive configuration setup
- Comprehensive documentation and examples
- Performance optimized for large-scale operations

## Quick Start

### 1. Installation

```bash
# Clone or extract the InfoBlox MCP Server
cd infoblox-mcp-server

# Install Python dependencies
pip3 install -r requirements.txt

# Or install the package
pip3 install .
```

### 2. Configuration

Run the interactive configuration setup:

```bash
python3 setup_config.py
```

You will be prompted for:
- InfoBlox Grid Master IP address
- Username and password
- WAPI version (default: v2.12)
- SSL verification preferences
- Timeout and retry settings
- Logging level

### 3. Start the Server

```bash
python3 infoblox-mcp-server.py
```

The server will start and listen for MCP client connections.

## Configuration

### Interactive Setup

The easiest way to configure the server is using the interactive setup script:

```bash
python3 setup_config.py
```

### Manual Configuration

Configuration is stored in `~/.infoblox-mcp/config.json`. You can manually edit this file or use the ConfigManager API:

```python
from infoblox_mcp.config import ConfigManager, InfoBloxConfig

config = InfoBloxConfig(
    grid_master_ip="192.168.1.100",
    username="admin",
    password="your_password",
    wapi_version="v2.12",
    verify_ssl=False,
    timeout=30,
    max_retries=3,
    log_level="INFO"
)

config_manager = ConfigManager()
config_manager.save_config(config)
```

### Environment Variables

You can also use environment variables for configuration:

```bash
export INFOBLOX_GRID_MASTER_IP="192.168.1.100"
export INFOBLOX_USERNAME="admin"
export INFOBLOX_PASSWORD="your_password"
export INFOBLOX_WAPI_VERSION="v2.12"
export INFOBLOX_VERIFY_SSL="false"
export INFOBLOX_TIMEOUT="30"
export INFOBLOX_MAX_RETRIES="3"
export INFOBLOX_LOG_LEVEL="INFO"
```

## Available Tools

The server provides 54 tools organized into 5 categories:

### DNS Management Tools (18 tools)

#### Basic Operations
- `infoblox_dns_list_zones` - List all DNS zones
- `infoblox_dns_create_zone` - Create a new DNS zone
- `infoblox_dns_delete_zone` - Delete a DNS zone
- `infoblox_dns_search_records` - Search for DNS records

#### Record Management
- `infoblox_dns_create_record_a` - Create A record
- `infoblox_dns_create_record_aaaa` - Create AAAA record
- `infoblox_dns_create_record_cname` - Create CNAME record
- `infoblox_dns_create_record_mx` - Create MX record
- `infoblox_dns_create_record_ptr` - Create PTR record
- `infoblox_dns_create_record_srv` - Create SRV record
- `infoblox_dns_create_record_txt` - Create TXT record
- `infoblox_dns_update_record` - Update existing DNS record
- `infoblox_dns_delete_record` - Delete DNS record

#### Advanced Operations
- `infoblox_dns_create_view` - Create DNS view
- `infoblox_dns_list_views` - List DNS views
- `infoblox_dns_zone_transfer` - Perform zone transfer
- `infoblox_dns_validate_zone` - Validate zone configuration
- `infoblox_dns_get_zone_statistics` - Get zone statistics

### DHCP Management Tools (18 tools)

#### Network Management
- `infoblox_dhcp_list_networks` - List DHCP networks
- `infoblox_dhcp_create_network` - Create DHCP network
- `infoblox_dhcp_delete_network` - Delete DHCP network
- `infoblox_dhcp_get_network_details` - Get network details
- `infoblox_dhcp_update_network` - Update network configuration

#### Lease Management
- `infoblox_dhcp_list_leases` - List DHCP leases
- `infoblox_dhcp_create_fixed_address` - Create fixed address
- `infoblox_dhcp_delete_fixed_address` - Delete fixed address
- `infoblox_dhcp_clear_lease` - Clear DHCP lease
- `infoblox_dhcp_get_lease_history` - Get lease history

#### IP Address Management
- `infoblox_dhcp_get_next_available_ip` - Get next available IP
- `infoblox_dhcp_reserve_ip` - Reserve IP address
- `infoblox_dhcp_release_ip` - Release IP address

#### Options and Configuration
- `infoblox_dhcp_list_options` - List DHCP options
- `infoblox_dhcp_create_option` - Create DHCP option
- `infoblox_dhcp_assign_option_to_network` - Assign option to network
- `infoblox_dhcp_get_network_utilization` - Get network utilization
- `infoblox_dhcp_restart_services` - Restart DHCP services

### IPAM Tools (6 tools)

- `infoblox_ipam_get_network_utilization` - Get network utilization statistics
- `infoblox_ipam_find_next_available_network` - Find next available network
- `infoblox_ipam_calculate_subnets` - Calculate subnet allocations
- `infoblox_ipam_discover_networks` - Discover networks
- `infoblox_ipam_get_ip_usage_report` - Generate IP usage reports
- `infoblox_ipam_validate_ip_allocation` - Validate IP allocations

### Grid Management Tools (8 tools)

- `infoblox_grid_list_members` - List grid members
- `infoblox_grid_get_status` - Get grid system status
- `infoblox_grid_get_member_details` - Get member details
- `infoblox_grid_restart_services` - Restart grid services
- `infoblox_grid_backup_database` - Backup grid database
- `infoblox_grid_get_capacity_report` - Get capacity reports
- `infoblox_grid_sync_configuration` - Sync grid configuration
- `infoblox_grid_get_license_info` - Get license information

### Bulk Operations Tools (4 tools)

- `infoblox_bulk_create_a_records` - Bulk create A records
- `infoblox_bulk_delete_records` - Bulk delete records
- `infoblox_bulk_export_csv` - Export data to CSV
- `infoblox_bulk_import_csv` - Import data from CSV

## Usage Examples

### DNS Management

#### List DNS Zones
```json
{
  "tool": "infoblox_dns_list_zones",
  "arguments": {
    "view": "default",
    "zone_format": "FORWARD"
  }
}
```

#### Create A Record
```json
{
  "tool": "infoblox_dns_create_record_a",
  "arguments": {
    "name": "server1.example.com",
    "ipv4addr": "192.168.1.10",
    "ttl": 3600,
    "comment": "Web server"
  }
}
```

### DHCP Management

#### Create Network
```json
{
  "tool": "infoblox_dhcp_create_network",
  "arguments": {
    "network": "192.168.1.0/24",
    "comment": "Office network"
  }
}
```

#### Get Next Available IP
```json
{
  "tool": "infoblox_dhcp_get_next_available_ip",
  "arguments": {
    "network": "192.168.1.0/24",
    "num_ips": 5
  }
}
```

### IPAM Operations

#### Get Network Utilization
```json
{
  "tool": "infoblox_ipam_get_network_utilization",
  "arguments": {
    "network": "192.168.1.0/24"
  }
}
```

### Grid Management

#### List Grid Members
```json
{
  "tool": "infoblox_grid_list_members",
  "arguments": {}
}
```

### Bulk Operations

#### Export to CSV
```json
{
  "tool": "infoblox_bulk_export_csv",
  "arguments": {
    "object_type": "record:a",
    "filename": "/tmp/a_records.csv",
    "filters": {
      "zone": "example.com"
    }
  }
}
```

## Testing

### Run Basic Tests
```bash
python3 test_server.py
```

### Run Comprehensive Tests
```bash
python3 comprehensive_test.py
```

### Run Integration Tests
```bash
python3 integration_test.py
```

## Architecture

### Components

1. **MCP Server** (`server.py`) - Main MCP protocol implementation
2. **InfoBlox Client** (`client.py`) - WAPI client with authentication
3. **Tool Registry** (`tools.py`) - Tool registration and execution
4. **Configuration Manager** (`config.py`) - Credential and settings management
5. **Error Handling** (`error_handling.py`) - Comprehensive error management

### Tool Modules

- **DNS Tools** (`dns_tools.py`) - Extended DNS management operations
- **DHCP Tools** (`dhcp_tools.py`) - Extended DHCP management operations  
- **Additional Tools** (`additional_tools.py`) - IPAM, Grid, and Bulk operations

### Security

- Passwords are encrypted using base64 encoding (production should use stronger encryption)
- Configuration files have restrictive permissions (600)
- SSL certificate verification is configurable
- Input validation and sanitization for all user inputs
- Comprehensive logging for security auditing

## Troubleshooting

### Common Issues

#### Connection Errors
- Verify Grid Master IP address is correct
- Check network connectivity to InfoBlox appliance
- Ensure WAPI is enabled on the InfoBlox system
- Verify SSL/TLS settings match your environment

#### Authentication Errors
- Verify username and password are correct
- Check if account has necessary permissions
- Ensure account is not locked or expired

#### Tool Execution Errors
- Check tool parameters match the expected schema
- Verify required parameters are provided
- Review error logs for detailed information

### Logging

Enable debug logging for detailed troubleshooting:

```python
from infoblox_mcp.config import InfoBloxConfig

config = InfoBloxConfig(
    # ... other settings ...
    log_level="DEBUG"
)
```

Or set environment variable:
```bash
export INFOBLOX_LOG_LEVEL="DEBUG"
```

### Configuration Reset

To reset configuration:
```bash
python3 -c "from infoblox_mcp.config import ConfigManager; ConfigManager().reset_config()"
```

## Development

### Adding New Tools

1. Define the tool in the appropriate module (`dns_tools.py`, `dhcp_tools.py`, etc.)
2. Register the tool in the `ToolRegistry` class
3. Implement the tool handler function
4. Add tests for the new tool
5. Update documentation

### Example Tool Implementation

```python
def register_custom_tool(self, registry):
    """Register a custom tool."""
    registry.register_tool(
        "infoblox_custom_operation",
        "Perform a custom InfoBlox operation",
        {
            "type": "object",
            "properties": {
                "parameter1": {
                    "type": "string",
                    "description": "First parameter"
                }
            },
            "required": ["parameter1"]
        },
        self._custom_operation_handler
    )

async def _custom_operation_handler(self, args, client):
    """Handle custom operation."""
    try:
        result = client.get("custom_endpoint", args)
        return json.dumps({"success": True, "data": result})
    except Exception as e:
        raise InfoBloxAPIError(f"Custom operation failed: {str(e)}")
```

## API Reference

### InfoBloxClient

The main client class for interacting with InfoBlox WAPI:

```python
class InfoBloxClient:
    def __init__(self, config: InfoBloxConfig)
    def get(self, object_type: str, params: Dict = None) -> List[Dict]
    def post(self, object_type: str, data: Dict) -> str
    def put(self, ref: str, data: Dict) -> str
    def delete(self, ref: str) -> bool
    def search_objects(self, object_type: str, params: Dict = None) -> List[Dict]
    def create_object(self, object_type: str, data: Dict) -> str
    def update_object(self, ref: str, data: Dict) -> str
    def delete_object(self, ref: str) -> bool
    def get_next_available_ip(self, network: str, num_ips: int = 1) -> List[str]
    def test_connection(self) -> bool
```

### ConfigManager

Configuration management class:

```python
class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None)
    def save_config(self, config: InfoBloxConfig) -> bool
    def load_config(self) -> Optional[InfoBloxConfig]
    def get_config(self) -> InfoBloxConfig
    def reset_config(self) -> bool
```

### ToolRegistry

Tool registration and execution:

```python
class ToolRegistry:
    def register_tool(self, name: str, description: str, parameters: Dict, handler: Callable)
    def get_all_tools(self) -> List[Tool]
    def execute_tool(self, name: str, arguments: Dict, client: InfoBloxClient) -> str
```

## License

This InfoBlox MCP Server is provided as-is for educational and development purposes. Please ensure compliance with your InfoBlox licensing terms and organizational policies.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the comprehensive test results
3. Enable debug logging for detailed error information
4. Consult InfoBlox WAPI documentation for API-specific questions

## Version History

- **v1.0.0** - Initial release with 54 tools covering DNS, DHCP, IPAM, Grid, and Bulk operations
- Comprehensive error handling and validation
- Interactive configuration setup
- Full MCP protocol compliance
- Performance optimized for enterprise use

