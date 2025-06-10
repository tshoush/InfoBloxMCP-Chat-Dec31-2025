#!/bin/bash

# InfoBlox MCP Server Installation Script

set -e

echo "InfoBlox MCP Server Installation"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python version check passed: $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

echo "✓ pip3 is available"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "✓ Dependencies installed"

# Make scripts executable
chmod +x infoblox-mcp-server.py
chmod +x setup_config.py

echo "✓ Scripts made executable"

# Create log directory
mkdir -p logs
echo "✓ Log directory created"

# Run initial tests
echo "Running initial tests..."
python3 test_server.py

echo ""
echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run configuration setup: python3 setup_config.py"
echo "2. Start the server: python3 infoblox-mcp-server.py"
echo ""
echo "For detailed documentation, see DOCUMENTATION.md"

