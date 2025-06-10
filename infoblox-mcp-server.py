#!/usr/bin/env python3
"""Entry point script for InfoBlox MCP Server."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infoblox_mcp.server import main

if __name__ == "__main__":
    main()

