"""Performance and integration test for InfoBlox MCP Server."""

import asyncio
import time
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.tools import ToolRegistry


async def test_tool_performance():
    """Test tool registration and lookup performance."""
    print("Testing Tool Performance...")
    
    registry = ToolRegistry()
    
    # Test tool registration time
    start_time = time.time()
    tools = registry.get_all_tools()
    registration_time = time.time() - start_time
    
    print(f"✓ Tool registration time: {registration_time:.4f} seconds")
    print(f"✓ Total tools registered: {len(tools)}")
    
    # Test tool lookup performance
    tool_names = [tool.name for tool in tools]
    
    start_time = time.time()
    for _ in range(1000):
        # Simulate tool lookups
        for tool_name in tool_names[:10]:  # Test first 10 tools
            if tool_name in registry.tools:
                pass
    lookup_time = time.time() - start_time
    
    print(f"✓ Tool lookup performance: {lookup_time:.4f} seconds for 10,000 lookups")


async def test_tool_schemas():
    """Test tool schema validation."""
    print("Testing Tool Schemas...")
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    schema_errors = []
    
    for tool in tools:
        try:
            # Check required fields
            if not tool.name:
                schema_errors.append(f"{tool.name}: Missing name")
            
            if not tool.description:
                schema_errors.append(f"{tool.name}: Missing description")
            
            if not tool.inputSchema:
                schema_errors.append(f"{tool.name}: Missing input schema")
            
            # Check schema structure
            schema = tool.inputSchema
            if not isinstance(schema, dict):
                schema_errors.append(f"{tool.name}: Invalid schema type")
                continue
            
            if schema.get("type") != "object":
                schema_errors.append(f"{tool.name}: Schema type should be 'object'")
            
            if "properties" not in schema:
                schema_errors.append(f"{tool.name}: Missing properties in schema")
            
        except Exception as e:
            schema_errors.append(f"{tool.name}: Schema validation error: {str(e)}")
    
    if schema_errors:
        print(f"✗ Schema validation failed for {len(schema_errors)} tools:")
        for error in schema_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(schema_errors) > 5:
            print(f"  ... and {len(schema_errors) - 5} more errors")
    else:
        print(f"✓ All {len(tools)} tool schemas are valid")


async def test_tool_documentation():
    """Test tool documentation completeness."""
    print("Testing Tool Documentation...")
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    doc_issues = []
    
    for tool in tools:
        # Check description quality
        if len(tool.description) < 10:
            doc_issues.append(f"{tool.name}: Description too short")
        
        if not tool.description.endswith('.'):
            doc_issues.append(f"{tool.name}: Description should end with period")
        
        # Check parameter documentation
        schema = tool.inputSchema
        if "properties" in schema:
            for param_name, param_info in schema["properties"].items():
                if "description" not in param_info:
                    doc_issues.append(f"{tool.name}: Parameter '{param_name}' missing description")
                elif len(param_info["description"]) < 5:
                    doc_issues.append(f"{tool.name}: Parameter '{param_name}' description too short")
    
    if doc_issues:
        print(f"✗ Documentation issues found in {len(doc_issues)} cases:")
        for issue in doc_issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
        if len(doc_issues) > 5:
            print(f"  ... and {len(doc_issues) - 5} more issues")
    else:
        print(f"✓ All {len(tools)} tools have complete documentation")


async def test_tool_categorization():
    """Test tool categorization and naming consistency."""
    print("Testing Tool Categorization...")
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    # Analyze tool naming patterns
    categories = {}
    naming_issues = []
    
    for tool in tools:
        parts = tool.name.split('_')
        
        if len(parts) < 3:
            naming_issues.append(f"{tool.name}: Invalid naming pattern (should be infoblox_category_action)")
            continue
        
        if parts[0] != "infoblox":
            naming_issues.append(f"{tool.name}: Should start with 'infoblox'")
            continue
        
        category = parts[1]
        action = '_'.join(parts[2:])
        
        if category not in categories:
            categories[category] = []
        categories[category].append(action)
    
    print(f"✓ Found {len(categories)} tool categories:")
    for category, actions in categories.items():
        print(f"  - {category.upper()}: {len(actions)} tools")
    
    if naming_issues:
        print(f"✗ Naming issues found:")
        for issue in naming_issues:
            print(f"  - {issue}")
    else:
        print("✓ All tools follow consistent naming pattern")


async def generate_tool_inventory():
    """Generate a complete tool inventory."""
    print("Generating Tool Inventory...")
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    
    inventory = {
        "total_tools": len(tools),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "categories": {},
        "tools": []
    }
    
    # Categorize tools
    for tool in tools:
        parts = tool.name.split('_')
        category = parts[1] if len(parts) > 1 else "other"
        
        if category not in inventory["categories"]:
            inventory["categories"][category] = 0
        inventory["categories"][category] += 1
        
        # Add tool details
        tool_info = {
            "name": tool.name,
            "category": category,
            "description": tool.description,
            "required_parameters": [],
            "optional_parameters": []
        }
        
        # Analyze parameters
        schema = tool.inputSchema
        if "properties" in schema:
            required = schema.get("required", [])
            for param_name, param_info in schema["properties"].items():
                param_detail = {
                    "name": param_name,
                    "type": param_info.get("type", "unknown"),
                    "description": param_info.get("description", "No description")
                }
                
                if param_name in required:
                    tool_info["required_parameters"].append(param_detail)
                else:
                    tool_info["optional_parameters"].append(param_detail)
        
        inventory["tools"].append(tool_info)
    
    # Save inventory
    with open("/home/ubuntu/infoblox-mcp-server/tool_inventory.json", "w") as f:
        json.dump(inventory, f, indent=2)
    
    print(f"✓ Tool inventory saved to tool_inventory.json")
    print(f"✓ Total tools: {inventory['total_tools']}")
    print(f"✓ Categories: {', '.join(inventory['categories'].keys())}")


async def main():
    """Main test function."""
    print("InfoBlox MCP Server Integration Tests")
    print("=" * 45)
    
    await test_tool_performance()
    print()
    
    await test_tool_schemas()
    print()
    
    await test_tool_documentation()
    print()
    
    await test_tool_categorization()
    print()
    
    await generate_tool_inventory()
    
    print("\n" + "=" * 45)
    print("Integration tests completed")


if __name__ == "__main__":
    asyncio.run(main())

