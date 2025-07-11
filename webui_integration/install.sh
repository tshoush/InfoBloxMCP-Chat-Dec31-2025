#!/bin/bash

# InfoBlox Open WebUI Integration Installation Script

set -e

echo "InfoBlox Open WebUI Integration Installation"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "infoblox_function.py" ]; then
    print_error "infoblox_function.py not found. Please run this script from the webui_integration directory."
    exit 1
fi

print_status "Found InfoBlox function files"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

print_status "Python version check passed: $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    exit 1
fi

print_status "pip3 is available"

# Install Python dependencies
print_info "Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_warning "Some dependencies may have failed to install"
fi

# Check for InfoBlox MCP server
print_info "Checking for InfoBlox MCP server..."

if [ -f "../infoblox-mcp-server.py" ]; then
    print_status "Found InfoBlox MCP server in parent directory"
    export INFOBLOX_MCP_SERVER_PATH="python3 $(realpath ../infoblox-mcp-server.py)"
elif [ -f "../../infoblox-mcp-server.py" ]; then
    print_status "Found InfoBlox MCP server in grandparent directory"
    export INFOBLOX_MCP_SERVER_PATH="python3 $(realpath ../../infoblox-mcp-server.py)"
else
    print_warning "InfoBlox MCP server not found in expected locations"
    print_info "Please set INFOBLOX_MCP_SERVER_PATH environment variable manually"
fi

# Check environment variables
print_info "Checking environment variables..."

if [ -z "$INFOBLOX_MCP_SERVER_PATH" ]; then
    print_warning "INFOBLOX_MCP_SERVER_PATH not set"
else
    print_status "INFOBLOX_MCP_SERVER_PATH: $INFOBLOX_MCP_SERVER_PATH"
fi

# Check for LLM API keys
llm_keys_found=0

if [ ! -z "$OPENAI_API_KEY" ]; then
    print_status "OpenAI API key found"
    llm_keys_found=$((llm_keys_found + 1))
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    print_status "Anthropic API key found"
    llm_keys_found=$((llm_keys_found + 1))
fi

if [ ! -z "$GROQ_API_KEY" ]; then
    print_status "Groq API key found"
    llm_keys_found=$((llm_keys_found + 1))
fi

if [ ! -z "$TOGETHER_API_KEY" ]; then
    print_status "Together AI API key found"
    llm_keys_found=$((llm_keys_found + 1))
fi

if [ $llm_keys_found -eq 0 ]; then
    print_warning "No LLM API keys found. LLM fallback will be disabled."
    print_info "Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY"
else
    print_status "Found $llm_keys_found LLM API key(s)"
fi

# Create example configuration
print_info "Creating example configuration..."
python3 config.py
print_status "Example configuration created"

# Run tests
print_info "Running integration tests..."
if python3 test_integration.py; then
    print_status "Integration tests completed"
else
    print_warning "Some integration tests failed"
fi

# Check for Open WebUI
print_info "Checking for Open WebUI..."

if command -v open-webui &> /dev/null; then
    print_status "Open WebUI command found"
elif [ -d "$HOME/.local/share/open-webui" ] || [ -d "/opt/open-webui" ]; then
    print_status "Open WebUI installation detected"
else
    print_warning "Open WebUI not detected"
    print_info "Please ensure Open WebUI is installed and running"
fi

echo ""
echo "============================================"
echo "Installation Summary"
echo "============================================"

if [ $llm_keys_found -gt 0 ] && [ ! -z "$INFOBLOX_MCP_SERVER_PATH" ]; then
    print_status "Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Copy infoblox_function.py to your Open WebUI functions directory"
    echo "2. Restart Open WebUI"
    echo "3. Test with: 'list grid members' or 'show network 192.168.1.0/24 utilization'"
else
    print_warning "Installation completed with warnings"
    echo ""
    echo "Required actions:"
    
    if [ -z "$INFOBLOX_MCP_SERVER_PATH" ]; then
        echo "• Set INFOBLOX_MCP_SERVER_PATH environment variable"
        echo "  export INFOBLOX_MCP_SERVER_PATH='python3 /path/to/infoblox-mcp-server.py'"
    fi
    
    if [ $llm_keys_found -eq 0 ]; then
        echo "• Set at least one LLM API key:"
        echo "  export OPENAI_API_KEY='your-openai-key'"
        echo "  export ANTHROPIC_API_KEY='your-anthropic-key'"
        echo "  export GROQ_API_KEY='your-groq-key'"
        echo "  export TOGETHER_API_KEY='your-together-key'"
    fi
fi

echo ""
echo "Documentation:"
echo "• README.md - Complete setup and usage guide"
echo "• config.py - Configuration management"
echo "• test_integration.py - Test the integration"
echo ""
echo "For support, check the troubleshooting section in README.md"
