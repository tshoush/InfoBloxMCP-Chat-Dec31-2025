
import asyncio
import sys
import os
import json
import re
import shlex
import logging
import click
import urllib3
import difflib

# Suppress InsecureRequestWarning for cleaner CLI output
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.config import ConfigManager
from infoblox_mcp.client import InfoBloxClient, InfoBloxAPIError
from infoblox_mcp.tools import ToolRegistry
from infoblox_mcp.llm_client import LLMClient

# Configure logging to show only errors to keep chat clean
logging.basicConfig(level=logging.ERROR)

class MCPChat:
    def __init__(self):
        self.config_manager = ConfigManager()
        
        # Check for setup flag
        if "--setup" in sys.argv or "--config" in sys.argv:
            print("Starting configuration wizard...")
            self.config = self.config_manager.prompt_for_config()
            if self.config_manager.save_config(self.config):
                print("Configuration saved.")
            else:
                 print("Error saving config.")
                 sys.exit(1)
        else:
            self.config = self.config_manager.load_config()

        self.registry = ToolRegistry()
        self.client = None
        self.llm_client = LLMClient(self.config) if self.config else None
        
        if not self.config:
            print("Error: Configuration not found. Please run setup first.")
            sys.exit(1)

    async def start(self):
        print("\n=== InfoBlox MCP Chat ===")
        print("Connecting to server...")
        
        try:
            self.client = InfoBloxClient(self.config)
            self.client.test_connection()
            print(f"Connected to Grid Master: {self.config.grid_master_ip}")
            print("Type 'help' for available commands or 'exit' to quit.\n")
            
            await self._chat_loop()
            
        except Exception as e:
            print(f"Connection failed: {e}")
        finally:
            if self.client:
                # No close method on client currently, effectively handled by GC
                pass

    async def _chat_loop(self):
        while True:
            try:
                user_input = input("InfoBlox> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Goodbye!")
                    break
                    
                await self._process_command(user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    async def _process_command(self, text):
        text_lower = text.lower()
        
        # 1. HELP
        if text_lower == 'help':
            self._show_help()
            return

        # 2. LIST NETWORKS / UTILIZATION
        # Matches: "list networks", "show utilization", "network status"
        if re.search(r'(list|show|get)\s+(networks|utilization|status)', text_lower):
            print("Fetching network utilization...")
            await self._run_tool("infoblox_ipam_get_utilization_summary", {})
            return



        # 3. SEARCH ZONE
        # Matches: "search zone <name>", "find zone <name>"
        zone_match = re.search(r'(search|find)\s+zone\s+["\']?([^"\']+)["\']?', text_lower)
        if zone_match:
            zone_name = zone_match.group(2)
            print(f"Searching for zone: '{zone_name}'...")
            try:
                # Use partial match (~) for flexibility
                zones = self.client.search_objects("zone_auth", {"fqdn~": zone_name})
                print(json.dumps(zones, indent=2))
            except Exception as e:
                print(f"Error searching zones: {e}")
            return

        # 4. SEARCH MARSHA
        # Matches: "search marsha <value>", "find marsha <value>"
        marsha_match = re.search(r'(search|find).*marsha\s+["\']?([^"\']+)["\']?', text_lower)
        if marsha_match:
            value = marsha_match.group(2)
            print(f"Searching for networks with MARSHA='{value}'...")
            await self._run_tool("infoblox_search_marsha", {"marsha_value": value})
            return

        # 5. SMART SEARCH (Combined Tool)
        # Matches: "search <value>", "find <value>"
        search_match = re.search(r'^(search|find)\s+["\']?([^"\']+)["\']?$', text_lower)
        if search_match:
            term = search_match.group(2)
            await self._handle_smart_search(term)
            return

        # 6. IMPORT AWS
        # Matches: "import <file>" or "import <file> view <view>"
        
        # Try to match with view specified first
        view_match = re.search(r'import\s+["\']?(.+?)["\']?\s+(?:view|network view)\s+["\']?([^"\']+)["\']?$', text_lower)
        simple_match = re.search(r'import\s+(?:file\s+)?["\']?([^"\']+)["\']?$', text_lower)
        
        file_path = None
        network_view = "default"
        
        if view_match:
            file_path = view_match.group(1)
            network_view = view_match.group(2)
        elif simple_match:
            file_path = simple_match.group(1)
            
        if file_path:
            # Check if file exists
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                return

            print(f"Analyzing import file: {file_path} (View: {network_view})...")
            
            # Run analysis first
            analysis_args = {"file_name": file_path}
            if network_view != "default":
                analysis_args["network_view"] = network_view
                
            result_json = await self._run_tool("infoblox_aws_import_analysis", analysis_args, print_output=False)
            
            # Print Analysis Summary
            try:
                result = json.loads(result_json)
                print("\nAnalysis Summary:")
                print(f"Total Records: {result.get('total_records')}")
                print(f"Valid Records: {result.get('valid_records')}")
                print(f"Conflicts: {len(result.get('conflicts', []))}")
                print(f"Missing EAs: {len(result.get('missing_eas', []))}")
                
                # Show conflict details specifically if relevant
                if result.get('conflicts'):
                    print("\nConflict Details (Sample):")
                    for conflict in result['conflicts'][:3]:
                         print(f"  - {conflict.get('network')} in view '{conflict.get('network_view', 'unknown')}'")
                
                if result.get('valid_records', 0) > 0:
                    confirm = input("\nDo you want to proceed with import? (yes/no): ").lower()
                    if confirm in ['y', 'yes']:
                        print("Executing import...")
                        exec_args = {"file_name": file_path, "dry_run": False}
                        if network_view != "default":
                            exec_args["network_view"] = network_view
                        await self._run_tool("infoblox_aws_import_execute", exec_args)
                    else:
                        print("Import cancelled.")
                else:
                    print("\nNo valid records to import.")
            except Exception as e:
                print(f"Error parsing analysis result: {e}")
            
            return


        # 7. HISTORY (SPLUNK)
        # Matches: "history <object>"
        history_match = re.search(r'history\s+(?:of\s+)?["\']?([^"\']+)["\']?', text_lower)
        if history_match:
            obj_name = history_match.group(1)
            print(f"Searching Splunk history for '{obj_name}'...")
            
            result_json = await self._run_tool("infoblox_splunk_audit_search", {"object_name": obj_name}, print_output=False)
            
            try:
                data = json.loads(result_json)
                if "error" in data:
                    print(f"Error querying Splunk: {data['error']}")
                else:
                    events = data.get("events", [])
                    count = data.get("count", 0)
                    
                    print(f"\nFound {count} events in the last {data.get('days_back')} days:\n")
                    if count > 0:
                        # Header
                        print(f"{'Time':<25} {'User':<20} {'Action':<15} {'Object'}")
                        print("-" * 80)
                        
                        for event in events:
                            ts = event.get('_time', 'N/A')
                            user = event.get('admin_name', 'N/A')
                            action = event.get('action', 'N/A')
                            obj = event.get('object_name', 'N/A') # sometimes internal name
                            
                            # Clean up timestamp if ISO
                            if 'T' in ts: ts = ts.replace('T', ' ')[:19]
                            
                            print(f"{ts:<25} {user:<20} {action:<15} {obj}")
                    else:
                        print("No history found.")
            except Exception as e:
                print(f"Error processing Splunk results: {e}")
            return

        # 8. FUZZY MATCH CHECK
        if self._check_fuzzy_match(text_lower):
            return


        # 9. LLM FALLBACK
        await self._handle_llm_fallback(text)

    async def _handle_smart_search(self, term):
        """Perform smart search across multiple objects."""
        print(f"Smart Search: Looking for '{term}' across Zones, Networks, and MARSHA tags...")
        
        # 1. Search Zones (Native)
        zones = []
        try:
            zones = self.client.search_objects("zone_auth", {"fqdn~": term})
        except: pass

        # 2. Search MARSHA (Tool)
        marsha_networks_json = await self._run_tool("infoblox_search_marsha", {"marsha_value": term}, print_output=False)
        marsha_networks = []
        try:
            marsha_data = json.loads(marsha_networks_json)
            marsha_networks = marsha_data.get('networks', [])
        except: pass

        # 3. Search Networks by Comment (Native)
        comment_networks = []
        try:
            comment_networks = self.client.search_objects("network", {"comment~": term})
        except: pass

        # Aggregate Results
        combined_results = {
            "search_term": term,
            "matches": {
                "zones": zones,
                "marsha_networks": marsha_networks,
                "comment_networks": comment_networks
            }
        }
        
        # Print Combined Results
        print("\n=== Search Results ===")
        if not any([zones, marsha_networks, comment_networks]):
            print("No matches found.")
        else:
            print(json.dumps(combined_results, indent=2))

    async def _handle_llm_fallback(self, text):
        """Pass unknown command to LLM if configured."""
        if not self.llm_client or not self.llm_client.is_configured():
             print("I didn't understand that command. Type 'help' to see what I can do.")
             return
             
        print("Command not recognized. Asking AI Assistant...")
        
        try:
             # Get tools from registry
             tools = self.registry.get_all_tools()
             response = self.llm_client.generate_response(text, tools)
             
             if response["type"] == "text":
                 print("\nAI Response:")
                 print(response["content"])
                 
             elif response["type"] == "tool_call":
                 tool_name = response["tool_name"]
                 tool_args = response["tool_args"]
                 
                 print(f"\nAI suggests running: {tool_name}")
                 print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                 
                 confirm = input("Run this command? (y/n): ").lower()
                 if confirm in ['y', 'yes']:
                     await self._run_tool(tool_name, tool_args)
                 else:
                     print("Aborted.")
                     
             elif response["type"] == "error":
                 print(f"AI Error: {response['content']}")
                 
        except Exception as e:
            print(f"AI processing failed: {e}")

    def _check_fuzzy_match(self, text):
        """Check for close matches to known commands."""
        known_commands = {
            "list networks": "list networks",
            "show utilization": "list networks",
            "search zone": "search zone <name>",
            "find zone": "search zone <name>",
            "search marsha": "search marsha <value>",
            "import file": "import <file>",
            "history": "history <object>",
            "help": "help",
            "exit": "exit"
        }
        
        # Check against keys
        matches = difflib.get_close_matches(text, known_commands.keys(), n=1, cutoff=0.6)
        if matches:
            suggestion = matches[0]
            canonical = known_commands[suggestion]
            print(f"I didn't understand '{text}'. Did you mean '{canonical}'?")
            return True
        
        # Check if it looks like a typo'd 'search' command with args
        if ' ' in text:
            cmd = text.split()[0]
            cmd_matches = difflib.get_close_matches(cmd, ['search', 'find', 'list', 'import'], n=1, cutoff=0.7)
            if cmd_matches:
                print(f"Unknown command. Did you mean to use '{cmd_matches[0]}'?")
                return True
                
        return False

    async def _run_tool(self, tool_name, args, print_output=True):
        try:
            result = await self.registry.execute_tool(tool_name, args, self.client)
            if print_output:
                # Try to pretty print JSON
                try:
                    parsed = json.loads(result)
                    print(json.dumps(parsed, indent=2))
                except:
                    print(result)
            return result
        except Exception as e:
            print(f"Tool execution error: {e}")
            return None

    def _show_help(self):
        print("\nAvailable Commands:")
        print("  list networks              - Show network utilization summary")
        print("  search marsha <value>      - Find networks by MARSHA tag")
        print("  search <value>             - Search across Zones, Networks, and Tags")
        print("  import <filepath>          - Analyze and import AWS CSV file")
        print("  exit                       - Quit the chat\n")

if __name__ == "__main__":
    chat = MCPChat()
    asyncio.run(chat.start())
