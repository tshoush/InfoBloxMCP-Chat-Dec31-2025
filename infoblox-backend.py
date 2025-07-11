#!/usr/bin/env python3
"""
InfoBlox MCP Backend Server
Connects the web interface to the actual InfoBlox MCP server
"""

import json
import sys
import os
import asyncio
import csv
import io
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the actual MCP server components
try:
    from infoblox_mcp.tools import ToolRegistry
    from infoblox_mcp.client import InfoBloxClient
    from infoblox_mcp.config import InfoBloxConfig
    print("✅ Successfully imported InfoBlox MCP components")
except ImportError as e:
    print(f"❌ Error importing MCP components: {e}")
    ToolRegistry = None
    InfoBloxClient = None
    InfoBloxConfig = None

app = Flask(__name__)
CORS(app)

class InfoBloxMCPClient:
    def __init__(self):
        """Initialize the real InfoBlox MCP client."""
        self.tool_registry = None
        self.infoblox_client = None
        self._initialize_infoblox_connection()

    def _initialize_infoblox_connection(self):
        """Initialize connection to InfoBlox."""
        try:
            if not InfoBloxConfig or not InfoBloxClient or not ToolRegistry:
                print("❌ InfoBlox MCP components not available")
                return

            # Create configuration from environment variables or defaults
            # Try new IP first, fallback to old IP if needed
            primary_ip = os.environ.get('INFOBLOX_HOST', '172.20.10.15')
            fallback_ip = '172.20.3.145'
            username = os.environ.get('INFOBLOX_USERNAME', 'admin')
            password = os.environ.get('INFOBLOX_PASSWORD', 'infoblox')

            print(f"🔗 Attempting to connect to InfoBlox at {primary_ip} as {username}")

            # Try primary IP first
            grid_master_ip = primary_ip

            # Try to connect with primary IP first, then fallback
            success = False
            for attempt_ip in [primary_ip, fallback_ip]:
                try:
                    print(f"🔄 Trying to connect to {attempt_ip}...")
                    config = InfoBloxConfig(
                        grid_master_ip=attempt_ip,
                        username=username,
                        password=password,
                        wapi_version="v2.12.3",  # Correct WAPI version
                        verify_ssl=False,  # Disable SSL verification for testing
                        timeout=10,  # Shorter timeout for faster fallback
                        max_retries=1  # Fewer retries for faster fallback
                    )

                    # Initialize InfoBlox client with timeout
                    print(f"🔄 Initializing InfoBlox client for {attempt_ip}...")
                    self.infoblox_client = InfoBloxClient(config)

                    # Test connection with timeout
                    print(f"🔄 Testing InfoBlox connection to {attempt_ip}...")
                    if self.infoblox_client.test_connection():
                        print(f"✅ Successfully connected to InfoBlox at {attempt_ip}")

                        # Initialize tool registry
                        self.tool_registry = ToolRegistry()
                        print("✅ InfoBlox tools initialized")
                        success = True
                        break
                    else:
                        print(f"❌ Failed to connect to InfoBlox at {attempt_ip}")
                        if attempt_ip == fallback_ip:
                            print("❌ All connection attempts failed")
                        else:
                            print(f"🔄 Trying fallback IP {fallback_ip}...")

                except Exception as conn_e:
                    print(f"❌ Connection error to {attempt_ip}: {conn_e}")
                    if attempt_ip == fallback_ip:
                        print("❌ All connection attempts failed")
                    else:
                        print(f"🔄 Trying fallback IP {fallback_ip}...")
                    continue

            if not success:
                print("❌ Failed to connect to InfoBlox - will return error messages")

        except Exception as e:
            print(f"❌ Error initializing InfoBlox connection: {e}")
            print("⚠️  Backend will start without InfoBlox connection")
            self.infoblox_client = None
            self.tool_registry = None

    def call_mcp_server(self, tool_name, query_or_arguments=None):
        """Call the actual InfoBlox MCP tools."""
        try:
            if not self.tool_registry or not self.infoblox_client:
                return {"error": "InfoBlox connection not available. Please check configuration."}

            # Handle both query string and arguments dict
            if isinstance(query_or_arguments, str):
                query = query_or_arguments
                arguments = {}
            else:
                query = query_or_arguments.get('query', '') if isinstance(query_or_arguments, dict) else ''
                arguments = query_or_arguments if isinstance(query_or_arguments, dict) else {}

            # Map simplified tool names to actual MCP tool names
            tool_name_mapping = {
                'get_zones': 'infoblox_dns_list_zones',
                'get_networks': 'infoblox_dhcp_list_networks',
                'get_grid_members': 'infoblox_grid_list_members',
                'get_system_health': 'infoblox_grid_get_status',
                'get_host_records': 'infoblox_dns_search_records',
                'get_a_records': 'infoblox_dns_search_records',
                'get_network_utilization': 'infoblox_ipam_get_network_utilization',
                'get_comprehensive_network_info': 'infoblox_dhcp_get_network_details',
                'get_dhcp_leases': 'infoblox_dhcp_list_networks',
                'get_discovery_status': 'infoblox_grid_get_status',
                'get_dns_statistics': 'infoblox_grid_get_status',
                'get_dhcp_statistics': 'infoblox_grid_get_status',
                'get_system_info': 'infoblox_grid_get_status'
            }

            actual_tool_name = tool_name_mapping.get(tool_name)
            if not actual_tool_name:
                return {"error": f"Unknown tool: {tool_name}"}

            # Prepare arguments for specific tools
            tool_arguments = arguments.copy() if arguments else {}

            # Special handling for specific tools
            if tool_name == 'get_a_records':
                tool_arguments = {"record_type": "A"}
                if arguments and 'zone' in arguments:
                    tool_arguments['zone'] = arguments['zone']
            elif tool_name == 'get_host_records':
                tool_arguments = {"record_type": "A"}
            elif tool_name == 'get_network_utilization':
                # Extract network from query if not provided
                if not tool_arguments.get('network'):
                    # Try to extract network from query
                    import re
                    network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
                    if network_match:
                        tool_arguments = {"network": network_match.group(1)}
                    else:
                        # Default to first network we know exists
                        tool_arguments = {"network": "192.168.100.0/24"}

            # Execute the tool using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.tool_registry.execute_tool(actual_tool_name, tool_arguments, self.infoblox_client)
                )
                # Parse JSON result if it's a string
                if isinstance(result, str):
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return {"message": result}
                return result
            finally:
                loop.close()

        except Exception as e:
            return {"error": f"Failed to call InfoBlox tool {tool_name}: {str(e)}"}

mcp_client = InfoBloxMCPClient()

@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handle InfoBlox queries from the web interface"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        method = data.get('method', 'mcp')  # Default to MCP

        if method == 'mcp':
            # Use MCP Server approach
            return handle_mcp_query(query)
        elif method == 'direct_wapi':
            # Use Direct WAPI approach
            return handle_direct_wapi_query(query)
        else:
            return jsonify({
                'success': False,
                'response': f"❌ Unknown method: {method}"
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f"❌ Server error: {str(e)}"
        })

def handle_mcp_query(query):
    """Handle query through MCP server"""
    # Map natural language queries to MCP tools
    if 'dns zone' in query or 'zones' in query:
        result = mcp_client.call_mcp_server('get_zones', query)

    elif 'dhcp network' in query or 'networks' in query:
        result = mcp_client.call_mcp_server('get_networks', query)

    elif 'grid member' in query or 'members' in query:
        result = mcp_client.call_mcp_server('get_grid_members', query)

    elif 'host record' in query or 'hosts' in query:
        result = mcp_client.call_mcp_server('get_host_records', query)

    elif 'a record' in query and 'example.com' in query:
        result = mcp_client.call_mcp_server('get_a_records', {'zone': 'example.com', 'query': query})

    elif 'utilization' in query or 'usage' in query:
        result = mcp_client.call_mcp_server('get_network_utilization', query)

    elif 'network info' in query or 'network details' in query or 'extended attributes' in query:
        # Extract network from query or prompt for selection
        import re
        network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
        if network_match:
            network = network_match.group(1)
            result = mcp_client.call_mcp_server('get_comprehensive_network_info', {'network': network})
        elif 'all' in query.lower():
            # Get all networks - use the networks list tool instead
            result = mcp_client.call_mcp_server('get_networks', query)
        else:
            # No specific network provided - return selection prompt
            result = {
                "selection_prompt": True,
                "message": "Please specify a network or select an option:",
                "options": [
                    {"value": "all", "label": "All Networks", "description": "Show comprehensive info for all networks"},
                    {"value": "prompt", "label": "Enter Network", "description": "Enter a specific network (e.g., 192.168.100.0/24)"},
                    {"value": "range", "label": "Enter Range", "description": "Enter a network range (e.g., 192.168.0.0/16)"}
                ],
                "examples": [
                    "show network info all",
                    "show network info for 192.168.100.0/24",
                    "show extended attributes for 10.0.0.0/8"
                ]
            }

    elif 'lease' in query or 'dhcp lease' in query:
        result = mcp_client.call_mcp_server('get_dhcp_leases', query)

    elif 'health' in query or 'status' in query:
        result = mcp_client.call_mcp_server('get_system_health', query)

    elif 'discovery' in query:
        result = mcp_client.call_mcp_server('get_discovery_status', query)

    elif 'statistics' in query or 'stats' in query:
        if 'dns' in query:
            result = mcp_client.call_mcp_server('get_dns_statistics', query)
        else:
            result = mcp_client.call_mcp_server('get_dhcp_statistics', query)
    else:
        # Generic query - try to determine best tool
        result = mcp_client.call_mcp_server('get_system_info', query)

    return process_result(result, query, "MCP")

def handle_direct_wapi_query(query):
    """Handle query through direct WAPI calls"""
    try:
        if not mcp_client.infoblox_client:
            return {"error": "Direct WAPI connection not available"}

        client = mcp_client.infoblox_client

        # Map queries to direct WAPI calls
        if 'dns zone' in query or 'zones' in query:
            result = client.search_objects("zone_auth")

        elif 'dhcp network' in query or 'networks' in query:
            result = client.search_objects("network")

        elif 'grid member' in query or 'members' in query:
            result = client.search_objects("member")

        elif 'health' in query or 'status' in query:
            result = client.search_objects("grid")

        elif 'utilization' in query or 'usage' in query:
            # Get network utilization using proper WAPI approach
            result = get_network_utilization_direct(client, query)

        elif 'network info' in query or 'network details' in query or 'extended attributes' in query:
            # Get comprehensive network information including extended attributes
            import re
            network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
            if network_match or 'all' in query.lower():
                result = get_comprehensive_network_info_direct(client, query)
            else:
                # No specific network provided - return selection prompt
                result = {
                    "selection_prompt": True,
                    "message": "Please specify a network or select an option:",
                    "options": [
                        {"value": "all", "label": "All Networks", "description": "Show comprehensive info for all networks"},
                        {"value": "prompt", "label": "Enter Network", "description": "Enter a specific network (e.g., 192.168.100.0/24)"},
                        {"value": "range", "label": "Enter Range", "description": "Enter a network range (e.g., 192.168.0.0/16)"}
                    ],
                    "examples": [
                        "show network info all",
                        "show network info for 192.168.100.0/24",
                        "show extended attributes for 10.0.0.0/8"
                    ]
                }

        else:
            result = {"message": f"Direct WAPI query for: {query}"}

        return process_result(result, query, "Direct WAPI")

    except Exception as e:
        return {"error": f"Direct WAPI error: {str(e)}"}

def get_network_utilization_direct(client, query):
    """Get network utilization using direct WAPI calls"""
    try:
        # Extract network from query or use default
        import re
        network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
        target_network = network_match.group(1) if network_match else "192.168.100.0/24"

        # First get all networks to find the one we want
        networks = client.search_objects("network")

        utilization_data = []
        for network in networks:
            network_addr = network.get('network', '')
            if target_network == "all" or network_addr == target_network or target_network in network_addr:
                # Get basic network info
                network_info = {
                    'network': network_addr,
                    'comment': network.get('comment', 'No description'),
                    'network_view': network.get('network_view', 'default')
                }

                # Try to get usage statistics (this is a simplified approach)
                # In real InfoBlox, you'd use specific WAPI endpoints for utilization
                try:
                    # Get DHCP ranges for this network to estimate usage
                    ranges = client.search_objects("range", {"network": network_addr})
                    network_info['dhcp_ranges'] = len(ranges)

                    # Get fixed addresses
                    fixed_addrs = client.search_objects("fixedaddress", {"network": network_addr})
                    network_info['fixed_addresses'] = len(fixed_addrs)

                    # Calculate basic utilization estimate
                    import ipaddress
                    net = ipaddress.IPv4Network(network_addr, strict=False)
                    total_ips = net.num_addresses - 2  # Exclude network and broadcast
                    used_estimate = len(fixed_addrs)  # This is a simplified estimate

                    network_info['utilization_estimate'] = {
                        'total_ips': total_ips,
                        'used_ips_estimate': used_estimate,
                        'utilization_percent': (used_estimate / total_ips * 100) if total_ips > 0 else 0
                    }

                except Exception as e:
                    network_info['utilization_error'] = str(e)

                utilization_data.append(network_info)

        return {
            'networks': utilization_data,
            'query_network': target_network,
            'note': 'Direct WAPI utilization is estimated from fixed addresses and ranges'
        }

    except Exception as e:
        return {"error": f"Failed to get utilization: {str(e)}"}

def get_comprehensive_network_info_direct(client, query):
    """Get comprehensive network information including extended attributes using direct WAPI calls"""
    try:
        # Extract specific network from query or get all networks
        import re
        network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
        target_network = network_match.group(1) if network_match else None

        # Get networks with extended attributes
        search_params = {}
        if target_network:
            search_params["network"] = target_network

        # Request extended attributes and additional fields
        networks = client.search_objects("network", search_params)

        comprehensive_data = []
        for network in networks:
            network_addr = network.get('network', 'Unknown')

            # Get detailed network information
            network_info = {
                'network': network_addr,
                'network_view': network.get('network_view', 'default'),
                'comment': network.get('comment', 'No description'),
                '_ref': network.get('_ref', ''),
                'basic_info': {}
            }

            # Add all basic network attributes
            for key, value in network.items():
                if not key.startswith('_') and key not in ['network', 'network_view', 'comment']:
                    network_info['basic_info'][key] = value

            # Get extended attributes if available
            try:
                # Try to get the network object with extended attributes
                network_ref = network.get('_ref', '')
                if network_ref:
                    detailed_network = client.get(f"{network_ref}?_return_fields=extattrs")
                    if 'extattrs' in detailed_network:
                        network_info['extended_attributes'] = detailed_network['extattrs']
                    else:
                        network_info['extended_attributes'] = {}
            except Exception as e:
                network_info['extended_attributes_error'] = str(e)
                network_info['extended_attributes'] = {}

            # Get related DHCP information
            try:
                # Get DHCP ranges for this network
                ranges = client.search_objects("range", {"network": network_addr})
                network_info['dhcp_ranges'] = ranges

                # Get fixed addresses
                fixed_addrs = client.search_objects("fixedaddress", {"network": network_addr})
                network_info['fixed_addresses'] = fixed_addrs

                # Get DHCP options if any
                dhcp_options = client.search_objects("dhcpoption", {"network": network_addr})
                network_info['dhcp_options'] = dhcp_options

            except Exception as e:
                network_info['dhcp_info_error'] = str(e)

            # Calculate utilization
            try:
                import ipaddress
                net = ipaddress.IPv4Network(network_addr, strict=False)
                total_ips = net.num_addresses - 2  # Exclude network and broadcast
                used_ips = len(network_info.get('fixed_addresses', []))

                network_info['utilization_info'] = {
                    'total_ips': total_ips,
                    'used_ips': used_ips,
                    'available_ips': total_ips - used_ips,
                    'utilization_percent': (used_ips / total_ips * 100) if total_ips > 0 else 0
                }
            except Exception as e:
                network_info['utilization_error'] = str(e)

            comprehensive_data.append(network_info)

        return {
            'comprehensive_networks': comprehensive_data,
            'query_network': target_network or 'all',
            'total_networks': len(comprehensive_data),
            'note': 'Comprehensive network information including extended attributes via Direct WAPI'
        }

    except Exception as e:
        return {"error": f"Failed to get comprehensive network info: {str(e)}"}

def process_result(result, query, method):
    """Process and format the result"""
    # Format the response for the web interface
    if isinstance(result, dict) and 'error' in result:
        return jsonify({
            'success': False,
            'response': f"❌ Error ({method}): {result['error']}"
        })
    else:
        # Format the result as HTML
        formatted_response = format_infoblox_response(result, query)
        formatted_response += f"<br><br><em>📡 Method: {method}</em>"
        return jsonify({
            'success': True,
            'response': formatted_response
        })

def format_infoblox_response(data, query):
    """Format InfoBlox data for display in the web interface - SHOW ACTUAL DATA"""
    if not data:
        return "No data returned from InfoBlox."

    print(f"🔍 DEBUG: Formatting data: {data}")
    print(f"🔍 DEBUG: Data type: {type(data)}")

    # Handle MCP response format that contains zones/networks in nested structure
    if isinstance(data, dict):
        # Check if this is a zones response
        if 'zones' in data and isinstance(data['zones'], list):
            zones = data['zones']
            html = f"<strong>🌐 DNS Zones ({len(zones)} found):</strong><br><br>"
            for zone in zones:
                fqdn = zone.get('fqdn', 'Unknown')
                zone_format = zone.get('zone_format', 'Unknown')
                view = zone.get('view', 'default')
                html += f"• <strong>{fqdn}</strong> ({zone_format}) in view '{view}'<br>"
            return html

        # Check if this is a utilization response (Direct WAPI)
        elif 'networks' in data and isinstance(data['networks'], list) and 'note' in data and 'utilization' in data.get('note', ''):
            networks = data['networks']
            html = f"<strong>📊 Network Utilization ({len(networks)} networks analyzed):</strong><br><br>"
            for network in networks:
                network_addr = network.get('network', 'Unknown')
                comment = network.get('comment', 'No description')

                if 'utilization_estimate' in network:
                    util = network['utilization_estimate']
                    total_ips = util.get('total_ips', 0)
                    used_ips = util.get('used_ips_estimate', 0)
                    util_percent = util.get('utilization_percent', 0)

                    # Create utilization bar
                    bar_length = 20
                    filled = int(bar_length * util_percent / 100) if util_percent > 0 else 0
                    bar = "█" * filled + "░" * (bar_length - filled)

                    html += f"• <strong>{network_addr}</strong><br>"
                    html += f"  📈 Utilization: {util_percent:.1f}%<br>"
                    html += f"  📊 `{bar}` {used_ips:,}/{total_ips:,} IPs<br>"
                    html += f"  💬 {comment}<br><br>"
                else:
                    html += f"• <strong>{network_addr}</strong> - {comment}<br>"

            html += f"<em>ℹ️ {data.get('note', '')}</em>"
            return html

        # Check if this is a comprehensive network info response
        elif 'comprehensive_networks' in data and isinstance(data['comprehensive_networks'], list):
            networks = data['comprehensive_networks']
            html = f"<strong>🔍 Comprehensive Network Information ({len(networks)} networks):</strong><br><br>"

            for network in networks:
                network_addr = network.get('network', 'Unknown')
                comment = network.get('comment', 'No description')
                network_view = network.get('network_view', 'default')

                html += f"<div style='border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; border-radius: 6px; background: #f9f9f9;'>"
                html += f"<h3 style='color: #8B0000; margin: 0 0 1rem 0;'>🌐 {network_addr}</h3>"
                html += f"<p><strong>Description:</strong> {comment}</p>"
                html += f"<p><strong>Network View:</strong> {network_view}</p>"

                # Show utilization if available
                if 'utilization_info' in network:
                    util = network['utilization_info']
                    util_percent = util.get('utilization_percent', 0)
                    used_ips = util.get('used_ips', 0)
                    total_ips = util.get('total_ips', 0)

                    # Create utilization bar
                    bar_length = 20
                    filled = int(bar_length * util_percent / 100) if util_percent > 0 else 0
                    bar = "█" * filled + "░" * (bar_length - filled)

                    html += f"<p><strong>📊 Utilization:</strong> {util_percent:.1f}% - `{bar}` {used_ips:,}/{total_ips:,} IPs</p>"

                # Show extended attributes
                if 'extended_attributes' in network:
                    ext_attrs = network['extended_attributes']
                    if ext_attrs:
                        html += f"<p><strong>🏷️ Extended Attributes:</strong></p><ul>"
                        for attr_name, attr_data in ext_attrs.items():
                            attr_value = attr_data.get('value', 'N/A') if isinstance(attr_data, dict) else attr_data
                            html += f"<li><strong>{attr_name}:</strong> {attr_value}</li>"
                        html += "</ul>"
                    else:
                        html += f"<p><strong>🏷️ Extended Attributes:</strong> None</p>"

                # Show DHCP ranges
                if 'dhcp_ranges' in network:
                    ranges = network['dhcp_ranges']
                    if ranges:
                        html += f"<p><strong>🔗 DHCP Ranges ({len(ranges)}):</strong></p><ul>"
                        for range_obj in ranges[:3]:  # Show first 3 ranges
                            start_addr = range_obj.get('start_addr', 'N/A')
                            end_addr = range_obj.get('end_addr', 'N/A')
                            html += f"<li>{start_addr} - {end_addr}</li>"
                        if len(ranges) > 3:
                            html += f"<li><em>... and {len(ranges) - 3} more ranges</em></li>"
                        html += "</ul>"
                    else:
                        html += f"<p><strong>🔗 DHCP Ranges:</strong> None configured</p>"

                # Show fixed addresses
                if 'fixed_addresses' in network:
                    fixed_addrs = network['fixed_addresses']
                    if fixed_addrs:
                        html += f"<p><strong>📍 Fixed Addresses ({len(fixed_addrs)}):</strong></p><ul>"
                        for addr in fixed_addrs[:5]:  # Show first 5 addresses
                            ip_addr = addr.get('ipv4addr', 'N/A')
                            mac_addr = addr.get('mac', 'N/A')
                            html += f"<li>{ip_addr} ({mac_addr})</li>"
                        if len(fixed_addrs) > 5:
                            html += f"<li><em>... and {len(fixed_addrs) - 5} more addresses</em></li>"
                        html += "</ul>"
                    else:
                        html += f"<p><strong>📍 Fixed Addresses:</strong> None configured</p>"

                # Show basic info
                if 'basic_info' in network and network['basic_info']:
                    html += f"<p><strong>ℹ️ Additional Properties:</strong></p><ul>"
                    for key, value in network['basic_info'].items():
                        if value and str(value).strip():
                            html += f"<li><strong>{key}:</strong> {value}</li>"
                    html += "</ul>"

                html += "</div>"

            html += f"<br><em>ℹ️ {data.get('note', '')}</em>"
            return html

        # Check if this is a networks response
        elif 'networks' in data and isinstance(data['networks'], list):
            networks = data['networks']
            html = f"<strong>🔗 DHCP Networks ({len(networks)} found):</strong><br><br>"
            for network in networks:
                network_addr = network.get('network', 'Unknown')
                comment = network.get('comment', 'No description')
                network_view = network.get('network_view', 'default')
                html += f"• <strong>{network_addr}</strong> - {comment} (view: {network_view})<br>"
            return html

        # Check if this is a records response
        elif 'records' in data and isinstance(data['records'], list):
            records = data['records']
            record_type = data.get('record_type', 'DNS')
            html = f"<strong>📝 {record_type} Records ({len(records)} found):</strong><br><br>"
            for record in records:
                name = record.get('name', 'Unknown')
                if 'ipv4addr' in record:
                    html += f"• <strong>{name}</strong> → {record['ipv4addr']}<br>"
                elif 'ipv6addr' in record:
                    html += f"• <strong>{name}</strong> → {record['ipv6addr']}<br>"
                else:
                    html += f"• <strong>{name}</strong><br>"
            return html

        # Special handling for grid status
        elif 'grid_info' in data or 'status' in data:
            html = "<strong>⚡ Grid System Status:</strong><br><br>"

            if 'status' in data:
                status = data['status']
                status_icon = "✅" if status == "operational" else "⚠️"
                html += f"• <strong>System Status:</strong> {status_icon} {status.title()}<br>"

            if 'grid_info' in data and isinstance(data['grid_info'], list):
                grid_items = data['grid_info']
                html += f"• <strong>Grid Members:</strong> {len(grid_items)} found<br>"
                for item in grid_items:
                    if isinstance(item, dict) and '_ref' in item:
                        # Extract meaningful info from grid reference
                        ref = item['_ref']
                        if 'Infoblox' in ref:
                            html += f"  - InfoBlox Grid Master (Active)<br>"
                        else:
                            html += f"  - Grid Member: {ref.split('/')[-1]}<br>"

            return html

        # Check if this is a selection prompt
        elif 'selection_prompt' in data and data['selection_prompt']:
            html = f"<strong>🤔 {data.get('message', 'Please make a selection:')}</strong><br><br>"

            if 'options' in data:
                html += "<div style='margin: 1rem 0;'>"
                for option in data['options']:
                    value = option.get('value', '')
                    label = option.get('label', value)
                    description = option.get('description', '')
                    html += f"<div style='border: 1px solid #ddd; padding: 0.5rem; margin: 0.5rem 0; border-radius: 4px; cursor: pointer;' onclick=\"setQuery('show network info {value}')\">"
                    html += f"<strong>{label}</strong><br><small>{description}</small>"
                    html += "</div>"
                html += "</div>"

            if 'examples' in data:
                html += "<strong>💡 Examples:</strong><br>"
                for example in data['examples']:
                    html += f"• <span style='cursor: pointer; color: #8B0000;' onclick=\"setQuery('{example}')\">{example}</span><br>"

            return html

        # Generic dict formatting - show all actual data
        else:
            html = "<strong>📊 InfoBlox Response:</strong><br><br>"
            for key, value in data.items():
                if isinstance(value, list):
                    html += f"• <strong>{key}:</strong> {len(value)} items<br>"
                    # Show first few items if it's a list
                    for _, item in enumerate(value[:3]):
                        if isinstance(item, dict):
                            # Show key fields from each item
                            item_desc = []
                            for field in ['fqdn', 'name', 'network', 'host_name']:
                                if field in item:
                                    item_desc.append(f"{field}: {item[field]}")
                            if item_desc:
                                html += f"  - {', '.join(item_desc)}<br>"
                            else:
                                html += f"  - {str(item)[:50]}...<br>"
                        else:
                            html += f"  - {str(item)}<br>"
                    if len(value) > 3:
                        html += f"  - ... and {len(value) - 3} more<br>"
                elif isinstance(value, dict):
                    html += f"• <strong>{key}:</strong> Object with {len(value)} fields<br>"
                else:
                    html += f"• <strong>{key}:</strong> {value}<br>"
            return html

    elif isinstance(data, list):
        # Direct list of items
        html = f"<strong>📋 Results ({len(data)} items):</strong><br><br>"
        for item in data:
            if isinstance(item, dict):
                # Show key fields
                key_field = next((k for k in ['fqdn', 'name', 'network', 'host_name'] if k in item), None)
                if key_field:
                    html += f"• <strong>{item[key_field]}</strong>"
                    # Add additional context
                    if 'zone_format' in item:
                        html += f" ({item['zone_format']})"
                    if 'comment' in item:
                        html += f" - {item['comment']}"
                    html += "<br>"
                else:
                    html += f"• {str(item)[:100]}...<br>"
            else:
                html += f"• {str(item)}<br>"
        return html

    else:
        # Simple string or other data
        return f"<strong>📋 Raw Result:</strong><br><br>{str(data)}"

@app.route('/')
def index():
    """Main web interface"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InfoBlox MCP Server - Marriott Corporate</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: #333;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-bottom: 3px solid #8B0000;
        }

        .header h1 {
            color: #8B0000;
            font-size: 2rem;
            font-weight: 600;
        }

        .header p {
            color: #666;
            margin-top: 0.5rem;
        }

        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 4px solid #8B0000;
        }

        .query-section {
            margin-bottom: 2rem;
        }

        .query-section h2 {
            color: #8B0000;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .input-group {
            margin-bottom: 1rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }

        input[type="text"], select {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #8B0000;
        }

        .method-selector {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .method-option {
            flex: 1;
            padding: 1rem;
            border: 2px solid #ddd;
            border-radius: 6px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }

        .method-option:hover {
            border-color: #8B0000;
            background: #f8f8f8;
        }

        .method-option.active {
            border-color: #8B0000;
            background: #8B0000;
            color: white;
        }

        .btn {
            background: #8B0000;
            color: white;
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s;
        }

        .btn:hover {
            background: #660000;
        }

        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .response-section {
            margin-top: 2rem;
        }

        .response-content {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 1.5rem;
            min-height: 200px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
        }

        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }

        .error {
            color: #dc3545;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
        }

        .success {
            color: #155724;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
        }

        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .quick-action {
            background: white;
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }

        .quick-action:hover {
            border-color: #8B0000;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .quick-action h3 {
            color: #8B0000;
            margin-bottom: 0.5rem;
        }

        .quick-action p {
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏨 InfoBlox MCP Server - Marriott Corporate</h1>
        <p>Network Infrastructure Management & DNS/DHCP Operations</p>
    </div>

    <div class="container">
        <div class="card">
            <div class="query-section">
                <h2>🔍 InfoBlox Query Interface</h2>

                <div class="quick-actions">
                    <div class="quick-action" onclick="setQuery('show network utilization')">
                        <h3>📊 Network Utilization</h3>
                        <p>View IP address usage statistics</p>
                    </div>
                    <div class="quick-action" onclick="setQuery('show comprehensive network info')">
                        <h3>🔍 Network Details</h3>
                        <p>Complete network info with extended attributes</p>
                    </div>
                    <div class="quick-action" onclick="setQuery('list dns zones')">
                        <h3>🌐 DNS Zones</h3>
                        <p>Show all DNS zones</p>
                    </div>
                    <div class="quick-action" onclick="setQuery('list dhcp networks')">
                        <h3>🔗 DHCP Networks</h3>
                        <p>Display DHCP network configurations</p>
                    </div>
                    <div class="quick-action" onclick="setQuery('show grid members')">
                        <h3>🖥️ Grid Members</h3>
                        <p>List InfoBlox grid members</p>
                    </div>
                </div>

                <div class="input-group">
                    <label for="query">Enter your InfoBlox query:</label>
                    <input type="text" id="query" placeholder="e.g., show network utilization, list dns zones, get dhcp leases" />
                </div>

                <div class="input-group">
                    <label>Query Method:</label>
                    <div class="method-selector">
                        <div class="method-option active" data-method="mcp" onclick="selectMethod('mcp')">
                            <strong>🔧 MCP Server</strong><br>
                            <small>Use InfoBlox MCP tools</small>
                        </div>
                        <div class="method-option" data-method="direct_wapi" onclick="selectMethod('direct_wapi')">
                            <strong>🔗 Direct WAPI</strong><br>
                            <small>Direct InfoBlox API calls</small>
                        </div>
                    </div>
                </div>

                <div style="display: flex; gap: 1rem; align-items: center;">
                    <button class="btn" onclick="executeQuery()">🚀 Execute Query</button>
                    <button class="btn" onclick="downloadJSON()" id="downloadJSON" style="display: none; background: #28a745;">📥 Download JSON</button>
                    <button class="btn" onclick="downloadCSV()" id="downloadCSV" style="display: none; background: #17a2b8;">📊 Download CSV</button>
                </div>
            </div>

            <div class="response-section">
                <h2>📋 Response</h2>
                <div id="response" class="response-content">
                    Ready to execute InfoBlox queries...
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedMethod = 'mcp';
        let lastQueryData = null;

        function selectMethod(method) {
            selectedMethod = method;
            document.querySelectorAll('.method-option').forEach(el => {
                el.classList.remove('active');
            });
            document.querySelector(`[data-method="${method}"]`).classList.add('active');
        }

        function setQuery(query) {
            document.getElementById('query').value = query;
        }

        function showDownloadButtons() {
            document.getElementById('downloadJSON').style.display = 'inline-block';
            document.getElementById('downloadCSV').style.display = 'inline-block';
        }

        function hideDownloadButtons() {
            document.getElementById('downloadJSON').style.display = 'none';
            document.getElementById('downloadCSV').style.display = 'none';
        }

        async function executeQuery() {
            const query = document.getElementById('query').value.trim();
            if (!query) {
                alert('Please enter a query');
                return;
            }

            const responseEl = document.getElementById('response');
            responseEl.innerHTML = '<div class="loading">🔄 Executing query...</div>';
            hideDownloadButtons();

            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        method: selectedMethod
                    })
                });

                const data = await response.json();

                if (data.success) {
                    responseEl.innerHTML = `
                        <div class="success">✅ Query executed successfully</div>
                        <div style="margin-top: 1rem;">${data.response}</div>
                    `;

                    // Store query data for downloads
                    lastQueryData = {
                        query: query,
                        method: selectedMethod
                    };

                    // Show download buttons
                    showDownloadButtons();
                } else {
                    responseEl.innerHTML = `
                        <div class="error">❌ Query failed: ${data.error || 'Unknown error'}</div>
                    `;
                    hideDownloadButtons();
                }
            } catch (error) {
                responseEl.innerHTML = `
                    <div class="error">❌ Network error: ${error.message}</div>
                `;
                hideDownloadButtons();
            }
        }

        async function downloadJSON() {
            if (!lastQueryData) {
                alert('No query data available for download');
                return;
            }

            try {
                const response = await fetch('/api/query/json', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(lastQueryData)
                });

                const result = await response.json();

                if (result.success) {
                    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `infoblox_data_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } else {
                    alert('Failed to generate JSON data: ' + result.error);
                }
            } catch (error) {
                alert('Error downloading JSON: ' + error.message);
            }
        }

        async function downloadCSV() {
            if (!lastQueryData) {
                alert('No query data available for download');
                return;
            }

            try {
                const response = await fetch('/api/query/csv', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(lastQueryData)
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `infoblox_data_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } else {
                    const result = await response.json();
                    alert('Failed to generate CSV data: ' + result.error);
                }
            } catch (error) {
                alert('Error downloading CSV: ' + error.message);
            }
        }

        // Allow Enter key to execute query
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeQuery();
            }
        });
    </script>
</body>
</html>
    '''

def handle_mcp_query_raw(query):
    """Handle query through MCP server and return raw data"""
    # Map natural language queries to MCP tools
    if 'dns zone' in query or 'zones' in query:
        result = mcp_client.call_mcp_server('get_zones', query)
    elif 'dhcp network' in query or 'networks' in query:
        result = mcp_client.call_mcp_server('get_networks', query)
    elif 'grid member' in query or 'members' in query:
        result = mcp_client.call_mcp_server('get_grid_members', query)
    elif 'host record' in query or 'hosts' in query:
        result = mcp_client.call_mcp_server('get_host_records', query)
    elif 'a record' in query and 'example.com' in query:
        result = mcp_client.call_mcp_server('get_a_records', {'zone': 'example.com', 'query': query})
    elif 'utilization' in query or 'usage' in query:
        result = mcp_client.call_mcp_server('get_network_utilization', query)
    elif 'network info' in query or 'network details' in query or 'extended attributes' in query:
        # Extract network from query or prompt for selection
        import re
        network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
        if network_match:
            network = network_match.group(1)
            result = mcp_client.call_mcp_server('get_comprehensive_network_info', {'network': network})
        elif 'all' in query.lower():
            # Get all networks - use the networks list tool instead
            result = mcp_client.call_mcp_server('get_networks', query)
        else:
            # No specific network provided - return selection prompt
            result = {
                "selection_prompt": True,
                "message": "Please specify a network or select an option:",
                "options": [
                    {"value": "all", "label": "All Networks", "description": "Show comprehensive info for all networks"},
                    {"value": "prompt", "label": "Enter Network", "description": "Enter a specific network (e.g., 192.168.100.0/24)"},
                    {"value": "range", "label": "Enter Range", "description": "Enter a network range (e.g., 192.168.0.0/16)"}
                ],
                "examples": [
                    "show network info all",
                    "show network info for 192.168.100.0/24",
                    "show extended attributes for 10.0.0.0/8"
                ]
            }
    elif 'lease' in query or 'dhcp lease' in query:
        result = mcp_client.call_mcp_server('get_dhcp_leases', query)
    elif 'health' in query or 'status' in query:
        result = mcp_client.call_mcp_server('get_system_health', query)
    elif 'discovery' in query:
        result = mcp_client.call_mcp_server('get_discovery_status', query)
    elif 'statistics' in query or 'stats' in query:
        if 'dns' in query:
            result = mcp_client.call_mcp_server('get_dns_statistics', query)
        else:
            result = mcp_client.call_mcp_server('get_dhcp_statistics', query)
    else:
        # Generic query - try to determine best tool
        result = mcp_client.call_mcp_server('get_system_info', query)

    return result

def handle_direct_wapi_query_raw(query):
    """Handle query through direct WAPI calls and return raw data"""
    try:
        if not mcp_client.infoblox_client:
            return {"error": "Direct WAPI connection not available"}

        client = mcp_client.infoblox_client

        # Map queries to direct WAPI calls
        if 'dns zone' in query or 'zones' in query:
            result = client.search_objects("zone_auth")
        elif 'dhcp network' in query or 'networks' in query:
            result = client.search_objects("network")
        elif 'grid member' in query or 'members' in query:
            result = client.search_objects("member")
        elif 'health' in query or 'status' in query:
            result = client.search_objects("grid")
        elif 'utilization' in query or 'usage' in query:
            result = get_network_utilization_direct(client, query)
        elif 'network info' in query or 'network details' in query or 'extended attributes' in query:
            import re
            network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', query)
            if network_match or 'all' in query.lower():
                result = get_comprehensive_network_info_direct(client, query)
            else:
                # No specific network provided - return selection prompt
                result = {
                    "selection_prompt": True,
                    "message": "Please specify a network or select an option:",
                    "options": [
                        {"value": "all", "label": "All Networks", "description": "Show comprehensive info for all networks"},
                        {"value": "prompt", "label": "Enter Network", "description": "Enter a specific network (e.g., 192.168.100.0/24)"},
                        {"value": "range", "label": "Enter Range", "description": "Enter a network range (e.g., 192.168.0.0/16)"}
                    ],
                    "examples": [
                        "show network info all",
                        "show network info for 192.168.100.0/24",
                        "show extended attributes for 10.0.0.0/8"
                    ]
                }
        else:
            result = {"message": f"Direct WAPI query for: {query}"}

        return result

    except Exception as e:
        return {"error": f"Direct WAPI error: {str(e)}"}

def convert_to_csv(data, query):
    """Convert InfoBlox data to CSV format"""
    output = io.StringIO()

    # Handle different data structures
    if isinstance(data, dict):
        if 'comprehensive_networks' in data:
            # Comprehensive network info
            networks = data['comprehensive_networks']
            if networks:
                fieldnames = ['network', 'network_view', 'comment', 'total_ips', 'used_ips', 'utilization_percent']

                # Add extended attributes columns
                all_ext_attrs = set()
                for network in networks:
                    if 'extended_attributes' in network:
                        all_ext_attrs.update(network['extended_attributes'].keys())

                fieldnames.extend(sorted(all_ext_attrs))
                fieldnames.extend(['dhcp_ranges_count', 'fixed_addresses_count'])

                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for network in networks:
                    row = {
                        'network': network.get('network', ''),
                        'network_view': network.get('network_view', ''),
                        'comment': network.get('comment', ''),
                        'total_ips': network.get('utilization_info', {}).get('total_ips', ''),
                        'used_ips': network.get('utilization_info', {}).get('used_ips', ''),
                        'utilization_percent': network.get('utilization_info', {}).get('utilization_percent', ''),
                        'dhcp_ranges_count': len(network.get('dhcp_ranges', [])),
                        'fixed_addresses_count': len(network.get('fixed_addresses', []))
                    }

                    # Add extended attributes
                    for attr in all_ext_attrs:
                        ext_attrs = network.get('extended_attributes', {})
                        if attr in ext_attrs:
                            attr_data = ext_attrs[attr]
                            row[attr] = attr_data.get('value', attr_data) if isinstance(attr_data, dict) else attr_data
                        else:
                            row[attr] = ''

                    writer.writerow(row)

        elif 'networks' in data:
            # Network utilization or basic networks
            networks = data['networks']
            if networks:
                fieldnames = ['network', 'comment', 'network_view']
                if 'utilization_estimate' in networks[0]:
                    fieldnames.extend(['total_ips', 'used_ips_estimate', 'utilization_percent'])

                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for network in networks:
                    row = {
                        'network': network.get('network', ''),
                        'comment': network.get('comment', ''),
                        'network_view': network.get('network_view', '')
                    }

                    if 'utilization_estimate' in network:
                        util = network['utilization_estimate']
                        row.update({
                            'total_ips': util.get('total_ips', ''),
                            'used_ips_estimate': util.get('used_ips_estimate', ''),
                            'utilization_percent': util.get('utilization_percent', '')
                        })

                    writer.writerow(row)

        elif 'zones' in data:
            # DNS zones
            zones = data['zones']
            if zones:
                fieldnames = ['fqdn', 'zone_format', 'view']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for zone in zones:
                    writer.writerow({
                        'fqdn': zone.get('fqdn', ''),
                        'zone_format': zone.get('zone_format', ''),
                        'view': zone.get('view', '')
                    })

        else:
            # Generic dict - convert to key-value pairs
            writer = csv.writer(output)
            writer.writerow(['Key', 'Value'])
            for key, value in data.items():
                writer.writerow([key, str(value)])

    elif isinstance(data, list):
        # Direct list of items
        if data:
            # Try to determine structure from first item
            first_item = data[0]
            if isinstance(first_item, dict):
                fieldnames = list(first_item.keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for item in data:
                    writer.writerow(item)
            else:
                writer = csv.writer(output)
                writer.writerow(['Value'])
                for item in data:
                    writer.writerow([str(item)])

    else:
        # Simple data
        writer = csv.writer(output)
        writer.writerow(['Data'])
        writer.writerow([str(data)])

    return output.getvalue()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'InfoBlox MCP Backend'})

@app.route('/api/query/json', methods=['POST'])
def handle_query_json():
    """Handle InfoBlox queries and return raw JSON data"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        method = data.get('method', 'mcp')

        if method == 'mcp':
            result = handle_mcp_query_raw(query)
        elif method == 'direct_wapi':
            result = handle_direct_wapi_query_raw(query)
        else:
            return jsonify({
                'success': False,
                'error': f"Unknown method: {method}"
            })

        return jsonify({
            'success': True,
            'data': result,
            'query': query,
            'method': method,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/query/csv', methods=['POST'])
def handle_query_csv():
    """Handle InfoBlox queries and return CSV data"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        method = data.get('method', 'mcp')

        if method == 'mcp':
            result = handle_mcp_query_raw(query)
        elif method == 'direct_wapi':
            result = handle_direct_wapi_query_raw(query)
        else:
            return jsonify({
                'success': False,
                'error': f"Unknown method: {method}"
            })

        # Convert to CSV
        csv_data = convert_to_csv(result, query)

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=infoblox_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def find_available_port(start_port=5001):
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

if __name__ == '__main__':
    print("🏨 Starting Marriott InfoBlox MCP Backend Server...")
    print("🔗 Initializing InfoBlox MCP connection...")

    # Initialize the MCP client
    mcp_client = InfoBloxMCPClient()

    port = find_available_port()
    if port:
        print(f"🚀 Starting Flask server on port {port}...")
        print(f"🌐 Access the API at: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        print("❌ Could not find an available port")
